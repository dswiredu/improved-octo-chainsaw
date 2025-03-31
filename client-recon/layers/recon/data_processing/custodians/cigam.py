import pandas as pd
import logging

from layers.recon.data_processing.custodians.custodian import Custodian
from layers.recon.datehandler import DateUtils
from layers.recon.exceptions import ClientDataNotFoundException

logger = logging.getLogger(__name__)


class CIGAM(Custodian):
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
        self.cigam_position_cols = {
            "portfolio": "account",
            "portfolio_name": "Portfolio Name",
            "instr_code": "instrument",
            "instr_name": "Instrument Name",
            "asset_class": "Asset Class",
            "price_currency": "Price Curr",
            "instr_curr": "Instrument Curr",
            "quantity": "custodian_units",
            "quote_date": "Price Date",
            "market_value": "custodian_mv_dirty",
            "accrued_interest": "CIGAM-AI",
            "cad_book_value": "custodian_bv",
            "quote": "custodian_price",
            "price_calc_rule": "price_calc_rule",
            "contract_size": "contract_size",
            "mortgage_factor": "mortgage_factor",
        }

    def get_feed_file(self, cigam_dte, file_type):
        file = f"{self.feed_path}/{cigam_dte}/{file_type}.txt"
        return file

    def apply_fx(self, fx, df: pd.DataFrame) -> pd.DataFrame:
        cad_usd = fx[fx["underly_ccy"] == "USD"].iloc[0]["exch_rate"]
        df["CAD_USD_fx_rate"] = 1
        usd_idx = df["Instrument Curr"] == "USD"
        df.loc[usd_idx, "CAD_USD_fx_rate"] = cad_usd
        return df

    def prep_file(self, cigam_dte, file_type) -> pd.DataFrame:
        s3_file = self.get_feed_file(cigam_dte, file_type)
        try:
            df = pd.read_csv(s3_file, sep="|", encoding="ISO-8859-1")
        except FileNotFoundError:
            msg = f"No data found for {self.firm}'s {file_type} file!"
            raise ClientDataNotFoundException(msg)
        if file_type == "positions":
            df = df[self.cigam_position_cols.keys()]
            df = df.rename(columns=self.cigam_position_cols)
        return df

    def read_data(self, dte: str) -> pd.DataFrame:
        recon_dte = DateUtils().get_recon_date(dte)
        cigam_dte = DateUtils.get_custodian_date(recon_dte)

        df = self.prep_file(cigam_dte, "positions")
        fx = self.prep_file(cigam_dte, "fx")

        df["date"] = pd.to_datetime(cigam_dte)

        df = self.apply_fx(fx, df)
        return df

    def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df["account"] = df["account"].astype(str).str.strip()
        df["custodian_mv_dirty"] = df["custodian_mv_dirty"] * df["CAD_USD_fx_rate"]
        df = df.replace("", 0, regex=True)
        df["Instrument Symbol"] = df["instrument"]
        df.drop_duplicates(
            keep="first", subset=["date", "account", "instrument"], inplace=True
        )
        df.fillna(0, inplace=True)
        return df

    def get_custdn_data(self, dte) -> pd.DataFrame:
        df = self.read_data(dte)
        res = self.process_data(df)
        return res
