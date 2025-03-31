import pandas as pd
import numpy as np
import logging

from layers.recon.data_processing.custodians.custodian import Custodian
from layers.recon.datehandler import DateUtils as dtU
from layers.recon.exceptions import ClientDataNotFoundException

logger = logging.getLogger(__name__)


class RBC(Custodian):
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

        self.rbc_holdings_cols = {
            "As_Of_Date": "date",
            "Acct_Num_KEY": "account",
            "Client_Sec_Num": "instrument",
            "Pos_Qty": "custodian_units_settle",
            "Daily_Loc_Ccy_Price": "custodian_price",
            "Settled_Acct_Ccy_Book_Val": "custodian_bv_acctCcy",
            "Settled_BookVal_AcctCcy": "bv_acctCcy",
            "Settled_Base_Ccy_Book_Val": "custodian_bv_baseCcy",
            "Settled_BookVal_BaseCcy": "bv_baseCcy",
            "Traded_BookVal_AcctCcy": "custodian_currency",
        }
        self.rbc_cash_cols = {
            "Book_Date": "date",
            "Acct_Num": "account",
            "Acct_Ccy": "instrument",
            "CBB_Combined_Amt": "custodian_units_settle",
        }

    def get_feed_file(self, rbc_dte, file_type):
        file = f"{self.feed_path}/{rbc_dte}/{file_type}.csv"
        return file

    def read_feed_file(self, rbc_dte, file_type: str) -> pd.DataFrame:
        s3_file = self.get_feed_file(rbc_dte, file_type)
        try:
            df = pd.read_csv(s3_file)
        except FileNotFoundError:
            msg = f"No data found for {self.firm}'s {file_type} file!"
            raise ClientDataNotFoundException(msg)
        if file_type == "AssetsHolding":
            df = df[self.rbc_holdings_cols.keys()]
            df = df.rename(columns=self.rbc_holdings_cols)
            df["instrument"] = df["instrument"].astype(str)
        else:
            df = df[self.rbc_cash_cols.keys()]
            df = df.rename(columns=self.rbc_cash_cols)
        return df

    def read_data(self, date: str) -> pd.DataFrame:
        recon_dte = dtU().get_recon_date(date)
        rbc_dte = dtU.get_custodian_date(recon_dte)

        holdings = self.read_feed_file(rbc_dte, "AssetsHolding")
        cash = self.read_feed_file(rbc_dte, "DailyCashSumm")

        df = pd.concat([holdings, cash], axis=0, ignore_index=True)
        df["account"] = df["account"].astype(str)
        df["date"] = pd.to_datetime(rbc_dte)
        return df

    @staticmethod
    def set_cash_values(df: pd.DataFrame) -> None:
        """
        Copy over cash units to cash market value and book value
        """
        cash_idx = df.instrument.isin(["CAD", "USD"])
        df.loc[cash_idx, "custodian_price"] = 1

    @staticmethod
    def get_custodian_book_values(df: pd.DataFrame, currency: str) -> None:
        df[f"custodian_bv_settle_{currency}"] = np.where(
            df.bv_acctCcy == currency, df.custodian_bv_acctCcy, np.nan
        )
        df[f"custodian_bv_settle_{currency}"] = np.where(
            df.bv_baseCcy == currency,
            df.custodian_bv_baseCcy,
            df[f"custodian_bv_settle_{currency}"],
        )
        df[f"custodian_bv_settle_{currency}"] = np.where(
            df.instrument == currency,
            df.custodian_units_settle,
            df[f"custodian_bv_settle_{currency}"],
        )

    def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        self.set_cash_values(df)
        self.get_custodian_book_values(df, "CAD")
        self.get_custodian_book_values(df, "USD")
        return df[self.custodian_return_cols]

    def get_custdn_data(self, dte) -> pd.DataFrame:
        df = self.read_data(dte)
        res = self.process_data(df)
        return res
