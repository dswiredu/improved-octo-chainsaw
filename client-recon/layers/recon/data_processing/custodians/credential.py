import pandas as pd
import numpy as np
import logging

from layers.recon.datehandler import DateUtils as dtU
from layers.recon.data_processing.custodians.custodian import Custodian
from layers.recon.exceptions import ClientDataNotFoundException

logger = logging.getLogger(__name__)


class Credential(Custodian):
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
        self.credential_col_map = {
            "AccountNumber": "account",
            "Cusip": "instrument",
            "Quantity": "custodian_units",
            "SecurityFundType": "currency",
            "CurCost": "custodian_bv",
            "MarketValue": "custodian_mv_clean",
        }

        self.str_col_map = {
            "position": ["AccountNumber", "Cusip"],
            "security_details": ["Cusip"],
        }

        self.use_col_map = {
            "position": self.credential_col_map.keys(),
            "security_details": [
                "Cusip",
                "LastTradePrice",
                "PriceDate",
                "BidPrice",
                "AskPrice",
                "FileDate",
            ],
        }

        self.cash_map = {"C": "CAD", "U": "USD"}

        self.date_col_map = {
            "security_details": ["PriceDate", "FileDate"],
        }

    def get_feed_file(self, credential_dte, file_type: str):
        file = f"{self.feed_path}/{credential_dte}/{file_type}.csv"
        return file

    def read_feed_file(self, credential_dte, file_type: str):
        file = self.get_feed_file(credential_dte, file_type)
        usecols = self.use_col_map.get(file_type)
        str_cols = self.str_col_map.get(file_type)
        date_cols = self.date_col_map.get(file_type)
        try:
            df = pd.read_csv(
                file,
                usecols=usecols,
                dtype={x: str for x in str_cols},
                parse_dates=date_cols,
                encoding="ISO-8859-1",
            )
            return df
        except FileNotFoundError:
            msg = f"Could not find {file_type} for {self.firm} at {file}!"
            raise ClientDataNotFoundException(msg)

    @staticmethod
    def get_instrument_details(
        positions: pd.DataFrame, security_details: pd.DataFrame
    ) -> pd.DataFrame:
        currentpx_idx = security_details["PriceDate"] >= security_details[
            "FileDate"
        ] - pd.Timedelta(days=1)
        current_prices = security_details[currentpx_idx]
        res = positions.merge(current_prices, on=["Cusip"], validate="m:1", how="left")
        return res

    def get_custodian_price(self, df: pd.DataFrame) -> pd.Series:
        prices = (
            df["LastTradePrice"].fillna(df["BidPrice"]).fillna(df["AskPrice"]).copy()
        )
        cash_idx = df.Cusip.isin(self.cash_map.values())
        prices.loc[cash_idx] = 1
        return prices

    def get_instrument(self, df: pd.DataFrame) -> pd.Series:
        """Credential sends Cash intruments as instrument 'cash'
        This needs to be converted to currency CAD or USD"""
        res = df["Cusip"].copy()
        cash_idx = res == "cash"
        res.loc[cash_idx] = df["SecurityFundType"].map(self.cash_map)
        return res

    def read_data(self, date: str) -> pd.DataFrame:
        recon_dte = dtU().get_recon_date(date)
        credential_dte = dtU.get_custodian_date(recon_dte)
        positions = self.read_feed_file(credential_dte, "position")
        security_details = self.read_feed_file(credential_dte, "security_details")
        res = self.get_instrument_details(positions, security_details)
        res["date"] = pd.to_datetime(credential_dte)
        return res

    def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df["Cusip"] = self.get_instrument(df)
        df["custodian_price"] = self.get_custodian_price(df)
        df.rename(columns=self.credential_col_map, inplace=True)
        df["custodian_bv_CAD"] = np.where(df.currency == "C", df.custodian_bv, np.nan)
        df["custodian_bv_CAD"] = np.where(
            df.instrument == "CAD", df.custodian_bv, df.custodian_bv_CAD
        )
        df["custodian_bv_USD"] = np.where(df.currency == "U", df.custodian_bv, np.nan)
        df["custodian_bv_USD"] = np.where(
            df.instrument == "USD", df.custodian_bv, df.custodian_bv_USD
        )
        return df[self.custodian_return_cols]

    def get_custdn_data(self, dte) -> pd.DataFrame:
        df = self.read_data(dte)
        res = self.process_data(df)
        return res
