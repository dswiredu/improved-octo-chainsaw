import pandas as pd
from datetime import datetime
import logging

from layers.recon.data_processing.custodians.custodian import Custodian
from layers.recon.datehandler import DateUtils, STD_DATE_FORMAT
from layers.recon.exceptions import (
    InputValidationException,
    ClientDataNotFoundException,
)

logger = logging.getLogger(__name__)


class NBIN(Custodian):
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
        self.currency_map = self.get_currency_map
        self.weedend_logic_clients = ["august", "ldic"]
        self.nbin_cols = [
            "RCREC10",
            "account",
            "raw_instrument",
            "Qty_referenced",
            "Amnt_referenced",
            "units",
            "amount",
            "BV_to_MV",
        ]

    def get_feed_file(self, nbin_dte):
        """
        Apparently the file name for all nbin clients is OUTPUTD.TXT
        """
        file = f"{self.feed_path}/{nbin_dte}/OUTPUTD.TXT"
        return file

    @property
    def get_currency_map(self) -> dict:
        df = pd.read_csv(
            "s3://d1g1t-custodian-data-ca/nbin/mapping-rules/NBINAccountCurrencyMapping.csv",
            index_col="Last digit",
            dtype=str,
        )
        res = self.currency_map_to_dict(df)
        return res

    @staticmethod
    def currency_map_to_dict(df: pd.DataFrame) -> dict:
        return df.to_dict()["Account Currency"]

    @staticmethod
    def get_nbin_units(df: pd.DataFrame) -> pd.Series:
        """df: custodian frame
        Use units unless Amnt_referenced column == 1"""

        res = df["units"].copy()
        amtref_idx = df["Amnt_referenced"] == 1
        res.loc[amtref_idx] = df["amount"]
        return res

    def get_cash_currency(self, df: pd.DataFrame) -> pd.Series:
        """df: custodian dataframe
        Missing secids represent cash in the account.
        Map all missing secIDs to a currency based on their last digit
        in currency map lookup"""

        res = df["stripped_instrument"].copy()
        iscash_idx = df["stripped_instrument"] == ""
        last_digits = df["account"].str[-1]
        res.loc[iscash_idx] = last_digits.map(self.currency_map)
        return res

    @staticmethod
    def process_cash_amounts_adhoc(df: pd.DataFrame) -> pd.Series:
        """df: custodian dataframe
        units is scaled down if it is for a cash instrument i.e units/100"""
        iscash_idx = df["instrument"].isin(["CAD", "USD"])
        res = df["initial_units"].copy()
        res.loc[iscash_idx] = df["initial_units"] / 100
        return res

    def read_data(self, date: str) -> pd.DataFrame:
        if date == DateUtils.get_last_cob_date():
            today = date
        else:
            if DateUtils.is_valid_date_input(date):
                today = datetime.strptime(date, STD_DATE_FORMAT)
            else:
                message = f"The input {date} is incorrect! Expected {STD_DATE_FORMAT}"
                raise InputValidationException(message)

        if self.firm in self.weedend_logic_clients and today.weekday() == 6:
            today = DateUtils.get_last_cob_date(today)
        nbin_dt = DateUtils.get_custodian_date(today)
        s3_file = self.get_feed_file(nbin_dt)
        try:
            df = pd.read_csv(s3_file, header=None)
        except FileNotFoundError:
            msg = f"No data found for {self.firm} at {s3_file}!"
            raise ClientDataNotFoundException(msg)
        df.columns = self.nbin_cols
        df["date"] = pd.to_datetime(date)
        return df

    def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df["stripped_instrument"] = df["raw_instrument"].str.strip()
        df["instrument"] = self.get_cash_currency(df)
        df["initial_units"] = self.get_nbin_units(df)
        df["custodian_units"] = self.process_cash_amounts_adhoc(df)
        return df

    def get_custdn_data(self, dte) -> pd.DataFrame:
        df = self.read_data(dte)
        processed_data = self.process_data(df)
        res = self.apply_firm_specific_logic(processed_data)
        return res[self.custodian_return_cols]
