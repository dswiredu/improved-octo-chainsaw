import pandas as pd
import logging

from layers.recon.data_processing.custodians.custodian import Custodian
from layers.recon.data_processing.lookup import CCY_MAP
from layers.recon.datehandler import DateUtils as dtU
from layers.recon.exceptions import ClientDataNotFoundException

logger = logging.getLogger(__name__)


class APX(Custodian):
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

        self.client_region_map = {
            "claret": "ca-central",
            "lmcg": "us-east",
            "gresham": "us-east",
        }

        self.apx_col_map = {
            "AccountCode": "account",
            "SecurityID": "instrument",
            "Current": "custodian_units",
            "Price": "custodian_price",
            "Lot": "tax_lot",
            "MV_Local": "custodian_mv_clean",
            "AI_Local": "custodian_ai",
            "Cost_Original": "custodian_bv",
            "Type": "SecTypeCode",
            "Symbol": "Symbol",
            "PrincipalCurrencyCode": "SecurityCurrency",
        }
        self.metric_cols = [
            "custodian_mv_clean",
            "custodian_price",
            "custodian_ai",
            "custodian_units",
            "custodian_bv",
        ]

        self.str_cols = ["AccountCode", "SecurityID", "Lot"]

    def get_feed_file(self, apx_dte):
        region = self.client_region_map.get(self.client, "us-east")
        file = f"s3://d1g1t-custodian-data-{region}-1/{self.custodian}/{self.firm}/{apx_dte}/Position.csv"
        return file

    def clean_apx_data(self, df: pd.DataFrame) -> None:
        for col in self.metric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    def aggregate_taxlots(self, df: pd.DataFrame) -> pd.DataFrame:
        agg_map = {
            "custodian_price": "first",
            "Symbol": "first",
            "SecurityCurrency": "first",
        }
        agg_map.update({x: sum for x in self.metric_cols if x != "custodian_price"})
        res = (
            df.groupby(["date", "account", "instrument", "SecTypeCode"])
            .agg(agg_map)
            .reset_index()
        )
        return res

    def read_data(self, date: str) -> pd.DataFrame:
        recon_dte = dtU().get_recon_date(date)
        apx_dte = dtU.get_custodian_date(recon_dte)
        s3_file = self.get_feed_file(apx_dte)
        try:
            usecols = self.apx_col_map.keys()
            dtype = {x: str for x in self.str_cols}
            df = pd.read_csv(s3_file, usecols=usecols, dtype=dtype)
        except FileNotFoundError:
            msg = f"No data found for {self.firm}'s Position file!"
            raise ClientDataNotFoundException(msg)
        df.rename(columns=self.apx_col_map, inplace=True)
        self.clean_apx_data(df)
        df["date"] = pd.to_datetime(apx_dte)
        return df

    @staticmethod
    def get_custodian_price(df: pd.DataFrame) -> pd.Series:
        cash_idx = df["SecTypeCode"].isin(
            ["ca", "uc"]
        )  # For both supervised and unsupervised cash.
        res = df["custodian_price"].copy()
        res.loc[cash_idx] = 1
        return res

    @staticmethod
    def set_apx_cash_instruments(df: pd.DataFrame) -> None:
        pure_cash_idx = (df["SecTypeCode"] + df["Symbol"]) == "cacash"
        df.loc[pure_cash_idx, "instrument"] = df["SecurityCurrency"].map(CCY_MAP)

    def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df["custodian_units"].fillna(df["custodian_bv"], inplace=True)
        df["custodian_price"] = self.get_custodian_price(df)
        self.set_apx_cash_instruments(df)
        res = self.aggregate_taxlots(df)
        return res

    def get_custdn_data(self, dte) -> pd.DataFrame:
        df = self.read_data(dte)
        processed_data = self.process_data(df)
        res = self.apply_firm_specific_logic(processed_data)
        return res
