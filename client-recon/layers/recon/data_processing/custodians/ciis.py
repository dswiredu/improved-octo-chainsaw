import pandas as pd
import logging

from layers.recon.data_processing.custodians.custodian import Custodian
from layers.recon.datehandler import DateUtils
from layers.recon.exceptions import ClientDataNotFoundException

logger = logging.getLogger(__name__)


class CIIS(Custodian):
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
        self.ciis_position_cols = {
            "AccountNumber": "account",
            "SecurityNumber": "instrument",
            "CustomerCode": "CustomerCode",
            "CurrencyCode": "Currency",
            "CurrentQuantity": "custodian_units",
            "MarketValue": "custodian_mv_dirty",
            "BookValue": "custodian_bv",
            "SecurityPrice": "custodian_price",
        }
        self.ciis_cash_cols = {
            "AccountNumber": "account",
            "CustomerCode": "CustomerCode",
            "CurrencyCode": "instrument",
            "TDBalance": "custodian_units",
        }

    def get_feed_file(self, ciis_dte, file_type):
        file = f"{self.feed_path}/{ciis_dte}/{file_type}.dat"
        return file

    def prep_file(self, ciis_dte, file_type: str) -> pd.DataFrame:
        s3_file = self.get_feed_file(ciis_dte, file_type)
        try:
            df = pd.read_csv(s3_file, sep="|", encoding="ISO-8859-1")
        except FileNotFoundError:
            msg = f"No data found for {self.firm}'s {file_type} file!"
            raise ClientDataNotFoundException(msg)
        if file_type == "EOD_StockRecord":
            df = df[self.ciis_position_cols.keys()]
            df = df.rename(columns=self.ciis_position_cols)
            df = df.drop(["custodian_bv"], axis=1)
        else:
            df = df[self.ciis_cash_cols.keys()]
            df = df.rename(columns=self.ciis_cash_cols)
            df["custodian_mv_dirty"] = df["custodian_units"].astype(float)
            df["custodian_price"] = 1
            df["Currency"] = df["instrument"]
        return df

    def read_data(self, dte: str) -> pd.DataFrame:
        recon_dte = DateUtils().get_recon_date(dte)
        ciis_dte = DateUtils.get_custodian_date(recon_dte)

        positions = self.prep_file(ciis_dte, "EOD_StockRecord")
        cash = self.prep_file(ciis_dte, "EOD_CashBalance")

        df = pd.concat([positions, cash], axis=0, ignore_index=True)

        df["date"] = pd.to_datetime(ciis_dte)
        return df

    def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df["account"] = df["account"].astype(str).str.strip()
        df["Settlement CCY"] = df["Currency"]
        return df

    def get_custdn_data(self, dte) -> pd.DataFrame:
        df = self.read_data(dte)
        processed_data = self.process_data(df)
        res = self.apply_firm_specific_logic(processed_data)
        return res
