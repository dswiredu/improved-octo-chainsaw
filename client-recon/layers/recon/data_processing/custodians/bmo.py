import pandas as pd
import logging
from datetime import datetime, timedelta

from layers.recon.data_processing.custodians.custodian import Custodian
from layers.recon.datehandler import DateUtils, STD_DATE_FORMAT
from layers.recon.exceptions import (
    InputValidationException,
    ClientDataNotFoundException,
)

logger = logging.getLogger(__name__)


class BMO(Custodian):
    def __init__(
        self,
        firm: str,
        client: str,
        custodian: str,
        feed: str,
        region: str,
        metrics: list,
    ) -> None:
        super().__init__(firm, client, custodian, feed, region, metrics)
        self.bmo_cols = {
            1: "account",
            2: "account_check_d1g1t",
            3: "account_type_code",
            5: "account_fund_portfolio_currency",
            6: "Internal Security Identifier",
            10: "bv_currency",
            13: "custodian_units",
            15: "custodian_mv_dirty",
            11: "custodian_bv_instr_cad_usd",
            14: "custodian_price",
        }

        self.numeric_cols = [
            "custodian_units",
            "custodian_mv_dirty",
            "custodian_bv_instr_cad_usd",
            "custodian_price",
        ]

        self.t_minus_one_clients = ["ldic"]

    def get_feed_file(self, bmo_dte):
        file = f"{self.feed_path}/{bmo_dte}/POSITION"
        return file

    @staticmethod
    def process_instruments(df: pd.DataFrame) -> None:
        subs = {
            "bmo_82": "USD",
            "bmo_86": "CAD",
            "bmo_K00009": "USD",
            "bmo_K00008": "CAD",
            "bmo_9999993": "USD",
            "bmo_9999992": "CAD",
        }
        df["instrument"] = "bmo_" + df["Internal Security Identifier"]
        df["instrument"].replace(subs, inplace=True)

    def lookup_bmo_date(self, date: str):
        # bmo data is t-2 due to late delivery; need custom date logic
        date_timestamp = datetime.strptime(date, "%Y-%m-%d")
        n = 1 if self.firm in self.t_minus_one_clients else 2
        if date == (datetime.today() + timedelta(-1)).strftime(STD_DATE_FORMAT):
            today = DateUtils.get_last_n_cob_date(n=n)
        else:
            if DateUtils.is_valid_date_input(date):
                today = datetime.strptime(date, STD_DATE_FORMAT)
            else:
                message = f"The input {date} is incorrect! Expected {STD_DATE_FORMAT}"
                raise InputValidationException(message)
        if self.firm == "august" and date_timestamp.weekday() in {4, 6}:
            today = DateUtils.get_last_cob_date(date_timestamp)
        return today

    def set_custodian_book_value_currency(self, df: pd.DataFrame):
        for currency in ["CAD", "USD"]:
            bv_currency_idx = df["bv_currency"] == currency
            df.loc[bv_currency_idx, f"custodian_bv_{currency}"] = df[
                "custodian_bv_instr_cad_usd"
            ]

    def read_data(self, date: str) -> pd.DataFrame:
        today = self.lookup_bmo_date(date)
        bmo_dte = DateUtils.get_custodian_date(today)
        s3_file = self.get_feed_file(bmo_dte)
        try:
            df = pd.read_csv(
                s3_file,
                dtype=str,
                skiprows=1,
                skipfooter=1,
                header=None,
                usecols=self.bmo_cols.keys(),
            )
        except FileNotFoundError:
            msg = f"No data found for {self.firm} at {s3_file}!"
            raise ClientDataNotFoundException(msg)
        df.rename(self.bmo_cols, axis=1, inplace=True)
        df["date"] = datetime.strptime(date, STD_DATE_FORMAT)
        return df

    def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        self.process_instruments(df)
        for col in self.numeric_cols:
            df.loc[:, col] = pd.to_numeric(df[col], errors="coerce")
        self.set_custodian_book_value_currency(df)
        # aggregate positions
        aggregated_df = (
            df.groupby(["account", "instrument", "date"]).sum(min_count=1).reset_index()
        )
        aggregated_df.loc[
            aggregated_df["instrument"].isin(["USD", "CAD"]),
            "custodian_price",
        ] = 1
        return aggregated_df[self.custodian_return_cols]

    def get_custdn_data(self, dte) -> pd.DataFrame:
        df = self.read_data(dte)
        processed_data = self.apply_firm_specific_logic(df)
        res = self.process_data(processed_data)
        return res
