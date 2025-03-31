from typing import Optional
import logging
import warnings

import pandas as pd
import numpy as np

from layers.recon.utils import get_ignored_accounts
from layers.recon.data_processing.d1g1t import get_d1g1t_client_data
from layers.recon.exceptions import MissingMetricException, InputValidationException
from layers.recon.data_processing.d1g1t import POSITION_INFO
from layers.recon.reporting import (
    send_recon_summary,
    generate_output_file,
    get_recon_output_filename,
)

warnings.filterwarnings("ignore", category=RuntimeWarning)

logger = logging.getLogger(__name__)


class OutlierDetection:
    def __init__(self, environment: str, client_info: dict) -> None:
        self.environment = environment
        self.client_info = client_info
        self.return_report_columns = POSITION_INFO + [
            "total_gain",
            "total_return",
            "return_outlier",
            "Note",
        ]
        self.mv_report_columns = [
            "date",
            "account",
            "mv_dirty_t-1",
            "mv_dirty_t",
            "mv_diff(%)",
            "market_value_outlier",
            "Note",
        ]
        self.mv_cols = ["mv_dirty_t-1", "mv_dirty_t"]

        self.outlier_type_map = {  # Add this to config in future
            "return": {"metric_col": "total_return", "threshold": 0.1},
            "market_value": {"metric_col": "mv_diff(%)", "threshold": 0.5},
        }

        self.ignored_accounts = get_ignored_accounts(
            self.client_info["ignore_accounts_file"]
        )

    @staticmethod
    def override_ignored_account_checks(
        df: pd.DataFrame, ignored_accounts: Optional[set], outlier_column: str
    ) -> None:
        """Set all breaks on accounts that are ignored to False and leaves a note."""
        df["Note"] = ""
        if ignored_accounts:
            note = "Account ignored during outlier detection."
            ignore_idx = df["account"].isin(ignored_accounts)
            df.loc[ignore_idx, outlier_column] = False
            df.loc[ignore_idx, "Note"] = note

    def check_for_outliers(
        self, df: pd.DataFrame, ignored_accounts: Optional[set], outlier_type: str
    ) -> None:
        outlier_info = self.outlier_type_map[outlier_type]
        outlier_col = outlier_info["metric_col"]
        threshold = outlier_info["threshold"]
        try:
            df[f"{outlier_type}_outlier"] = df[outlier_col].abs() >= threshold
            self.override_ignored_account_checks(df, ignored_accounts, outlier_col)
        except KeyError:
            msg = f"Column required to perform outlier detection ({outlier_col}) cannot be found in d1g1t data!"
            raise MissingMetricException(msg)

    @staticmethod
    def set_date_t_mv_dirty(df: pd.DataFrame, reporting_currency: str) -> None:
        """Market value in reporting currency is the mv for dirty T"""
        rename_cols = {f"d1g1t_mv_dirty_{reporting_currency}": "mv_dirty_t"}
        df.rename(columns=rename_cols, inplace=True)

    def get_account_level_market_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate market values to the account level"""
        res = df.groupby(["date", "account"])[self.mv_cols].sum().reset_index()
        return res

    def get_mv_pct_change(self, df: pd.DataFrame):
        """
        - Computes percentage change from previous to current date.
        - inf is filled with 1 since position was 0 before.
        - For missing values fills with 0 to represent no mv for both dates.
        """
        res = df[self.mv_cols].pct_change(axis=1)["mv_dirty_t"]
        res.replace([np.inf, -np.inf], 1, inplace=True)
        res.fillna(0, inplace=True)
        return res

    def get_account_mv_outlier_report(
        self, df: pd.DataFrame, reporting_currency: str
    ) -> pd.DataFrame:
        """
        - Date T-1 mv_dirty already exists (mv_dirty_t-1).
        - Get date T mv_dirty from reporting_currency
        - Aggregate market values to the account level.
        - Compute precent differences
        - Check for market value outliers using MV_THRESHOLD
        """
        self.set_date_t_mv_dirty(df, reporting_currency)
        res = self.get_account_level_market_values(df)
        res["mv_diff(%)"] = self.get_mv_pct_change(res)
        self.check_for_outliers(res, self.ignored_accounts, outlier_type="market_value")
        return res[self.mv_report_columns]

    def get_position_return_outlier_report(self, df: pd.DataFrame):
        """
        - df contains total_return and total_gain columns
        - Check for return outliers using MV_THRESHOLD
        """
        self.check_for_outliers(df, self.ignored_accounts, outlier_type="return")
        return df[self.return_report_columns]

    def run_outlier_detection(
        self,
        firm: str,
        client: str,
        client_version: str,
        dte: str,
        reporting_currency: str,
        custodian_aliases: dict,
        outlier_type: str,
    ) -> None:
        d1g1t_input_path = self.client_info["d1g1t_input_file_path"]
        output_paths = self.client_info["output_file_destination"].split(",")
        slack_webhook_urls = self.client_info["slack_webhook_URL"].split(",")
        recon_funds = self.client_info["recon_funds"]

        d1g1t_df = get_d1g1t_client_data(
            firm,
            client,
            d1g1t_input_path,
            self.environment,
            client_version,
            recon_funds,
            dte,
            reporting_currency,
            custodian_aliases,
        )

        if outlier_type == "return":
            res = self.get_position_return_outlier_report(d1g1t_df)
        elif outlier_type == "market_value":
            res = self.get_account_mv_outlier_report(d1g1t_df, reporting_currency)
        else:
            raise InputValidationException

        slack_path = output_paths[0]
        output_filename = get_recon_output_filename(
            self.environment, slack_path, client, dte, "", recon_type=outlier_type
        ).strip()

        for slack_channel in slack_webhook_urls:
            try:
                send_recon_summary(
                    res,
                    client,
                    dte,
                    output_filename,
                    self.client_info,
                    slack_channel.strip(),
                    recon_type=outlier_type,
                )
            except ValueError:
                msg = "slack channel is not provided for posting summary."
                logger.error(msg)
                logger.warning("Continuing...")

        for output_path in output_paths:
            output_filename = get_recon_output_filename(
                self.environment, output_path, client, dte, "", recon_type=outlier_type
            ).strip()
            generate_output_file(res, d1g1t_input_path, output_filename, client)


def run(
    firm: str,
    client: str,
    date: str,
    environment: str,
    client_version: str,
    client_info: dict,
    reporting_currency: str,
    custodian_aliases: dict,
    outlier_type: str,
):
    runner = OutlierDetection(environment, client_info)
    runner.run_outlier_detection(
        firm=firm,
        client=client,
        client_version=client_version,
        dte=date,
        reporting_currency=reporting_currency,
        custodian_aliases=custodian_aliases,
        outlier_type=outlier_type,
    )
