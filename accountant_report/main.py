"""
Script to run claret accountant report for a giving account(fpk).

Usage:
    python -m claret.accountant_report.main.py --server https://api-claret.d1g1t.com
                            -u david.wiredu@d1g1t.com
                            -a 315-12378-27
                            -s 2023-09-30
                            -e 2024-09-30
                            -r EvaluationReport
                            -o s3://d1g1t-client-ca/claret/accountant-reports
"""

import logging
import time
import os
import pathlib
from datetime import datetime, timedelta
from functools import cached_property

from openpyxl import Workbook
import pandas as pd
import i18n

from ps.base import PSMain
from exceptions import InputValidationError
import claret.accountant_report.reports as reports
from utils.main_utils import valid_date_input
from claret.accountant_report.lookup import currency_code_to_currency_name

LOG = logging.getLogger(__name__)


class AccountantReport(PSMain):
    """Class to handle Accountant report generation."""

    def __init__(self):
        super().__init__()
        self.start_date = self.args.start_date
        self.end_date = self.args.end_date
        self.output_location = self.args.output_location

    def add_extra_args(self):
        """Add extra cmd line arguments to the script."""

        self.parser.add_argument(
            "-a",
            "--account-fpk",
            type=str,
            help="Account firm provided key.",
            required=False,
        )
        self.parser.add_argument(
            "-l",
            "--lang-code",
            choices=["en", "fr"],
            default="en",
            help="Account firm provided key.",
            required=False,
        )
        self.parser.add_argument(
            "-f",
            "--accounts-file",
            type=str,
            help="Account file containing list of account fpks",
            required=False,
        )
        self.parser.add_argument(
            "-r",
            "--report-type",
            choices=reports.__all__,
            default=None,
            help="String representing which report to run.",
        )
        self.parser.add_argument(
            "-s",
            "--start-date",
            type=valid_date_input,
            help="Report run start date. Format 'YYYY-MM-DD'",
            required=True,
        )
        self.parser.add_argument(
            "-e",
            "--end-date",
            type=valid_date_input,
            help="Report run end date. Format 'YYYY-MM-DD'",
            required=True,
        )
        self.parser.add_argument(
            "-o",
            "--output-location",
            type=str,
            help="Local or s3 path to save output to",
            required=True,
        )

    @staticmethod
    def _get_report_workbook() -> Workbook:
        wb = Workbook()
        return wb

    def _save_report_workbook(self):
        del self._workbook["Sheet"]  # TODO: hack!
        self._workbook.save(self.report_filename)
    
    @cached_property
    def trxs_start_date(self) -> str:
        """For transactions reports this is the date to use."""
        date_str = self.args.start_date
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        trx_date = date_obj + timedelta(days=1)
        return trx_date.strftime("%Y-%m-%d")

    @property
    def reports_to_run(self):
        """Get a list of reports to run."""
        report = self.args.report_type
        return [report] if report else reports.__all__

    @property
    def _expected_report_sheet_names(self):
        """Gets the names of all reports that should be generated."""
        return [
            "Income",
            "Realized Gain-Losses FX",
            "Realized Gain-Losses",
            "Evaluation - Beginning",
            "Evaluation - End",
            "Taxprep - Schedule 6",
            "Taxprep - Schedule 3",
            "Deposits-Withdrawals-Fees",
            "Capital Transactions",
            "Non-cash Transactions",
        ]

    @property
    def all_reports_run_successfully(self):
        """Checks if all reports were run before reconciliation report."""
        return all(
            report in self._workbook.sheetnames for report in self._expected_report_sheet_names
        )

    @staticmethod
    def get_report_filename(account_fpk: str) -> str:
        """Returns output file name for excel."""
        today = datetime.today().strftime("%Y-%m-%d")
        return f"Claret_AccountantReport_{account_fpk}_{today}.xlsx"
    
    def get_translator(self, lang_code: str = 'en'):
        i18n.load_path.clear()

        dir_path = pathlib.Path(__file__).parent.resolve()
        translation_path = os.path.join(dir_path, "data", "translations")
        i18n.load_path.append(translation_path)
        
        i18n.set("file_format", "json")
        i18n.set("filename_format", "{locale}.{format}") 
        i18n.set("locale", lang_code)                       
        i18n.set("fallback", "en")                     
        i18n.set("deep_key_transformer", lambda k: k)

        # i18n.t("dummy") #Force-load the translation file (first .t() does that)
        return i18n.t



    @staticmethod
    def _parse_account_info(response: dict) -> None:
        response["currency"] = response["currency"].split("/")[-2]
        response["reporting_currency_name"] = currency_code_to_currency_name[
            response["currency"]
        ]

    def get_account_info(self, account_fpk: str) -> dict:
        """Make api call to get all account information."""
        api_call = self.api.data.accounts
        api_call._store["base_url"] += f"{account_fpk}/"
        response = api_call.get(extra="limit=10")
        if response:
            self._parse_account_info(response)
            return response
        raise InputValidationError(
            f"Could not get account info for fpk: {account_fpk}!"
        )

    @staticmethod
    def get_payload_file(payload_filename: str) -> str:
        """Gets calculation payload stored in data folder."""
        dir_path = pathlib.Path(__file__).parent.resolve()
        return os.path.join(dir_path, "data", "payloads", payload_filename)
    
    def get_accounts_list(self) -> set:
        if self.args.account_fpk:
            return {self.args.account_fpk}
        elif self.args.accounts_file:
            file = self.args.accounts_file
            df = pd.read_csv(file, dtype=str)
            return set(df["accounts"])
        else:
            raise InputValidationError("At least an account fpk or accounts list file must be provided!")
    
    def run_single_account_accountant_report(self, account_fpk: str) -> None:
        """Runs accountant report for a single account"""
        self.account_info = self.get_account_info(account_fpk)
        lang_code = self.account_info["user_defined_2"] or self.args.lang_code # Todo: Ensure client puts report generation currency in udf2!.
        self.translate = self.get_translator(lang_code)

        self.report_filename = self.get_report_filename(account_fpk)
        self._workbook = self._get_report_workbook()
        self.recon = dict()  # Gathers data for reconciliation

        for report_to_run in self.reports_to_run:
            LOG.info(f"Running {report_to_run} report for {account_fpk}...")
            try:
                report_cls = getattr(reports, report_to_run)
                report = report_cls(self)
                report.run()
            except Exception as err:
                LOG.error(f"Unexpected error running {report_to_run} report for {account_fpk}: {err}!")

        if self.all_reports_run_successfully:
            LOG.info(f"Running reconciliation report for {account_fpk}...")
            try:
                reports.Reconciliation(self).run()
            except Exception as err:
                LOG.error(f"Unexpected error running reconciliation report: {err}!")
        else:
            LOG.error(f"Could not run reconciliation report for {account_fpk} due to missing reports!")

        LOG.info(f"Saving report for {account_fpk} to {self.report_filename}...")
        self._save_report_workbook()


    def after_login(self):
        """After login gets the specific report and runs it"""
        start = time.time()
        self.accounts_list = self.get_accounts_list()
        for account_fpk in self.accounts_list:
            elapsed_time  = time.time() - start
            if elapsed_time >= 5: # 45 mins
                self.refresh_api_token()
                start = time.time()
            try:
                self.run_single_account_accountant_report(account_fpk)
            except Exception as err:
                LOG.error(f"Unexpected error running report for {account_fpk} : {err}")



if __name__ == "__main__":
    work = AccountantReport()
    work.main()
