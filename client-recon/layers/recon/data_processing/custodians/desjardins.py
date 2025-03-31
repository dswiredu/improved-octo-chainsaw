import pandas as pd
import logging

from datetime import timedelta
from layers.recon.datehandler import DateUtils as dtU
from layers.recon.data_processing.custodians.custodian import Custodian
from layers.recon.exceptions import ClientDataNotFoundException
from layers.recon.data_processing.d1g1t import SUPPORTED_CURRENCIES

logger = logging.getLogger(__name__)


class Desjardins(Custodian):
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
        self.djd_holdings_cols = [
            "Record Type",
            "Account Number",
            "Security",
            "Date Issued",
            "Annual Return",
            "Return %",
            "Maturity Date",
            "Country of Issue",
            "CUSIP",
            "SEDOL",
            "ISIN",
            "Interest Calculation Method",
            "Financial Instrument",
            "Country Exposure",
            "Category Financial Instrument",
            "Sub-Category Financial Instrument",
            "Security Currency",
            "Quantity",
            "Position Type",
            "Average Unit Cost Security Currency",
            "Book Value Security Currency",
            "Accrued Interest Security Currency",
            "Last Price Security Currency",
            "Market Value Security Currency",
            "Account Currency",
            "Book Value Account Currency",
            "Accrued Interest Account Currency",
            "Market Value Account Currency",
            "Exchange Rate Security Currency to Account Currency",
            "Asset Allocation %",
            "Fair Value Hierarchy",
        ]

        self.holdings_str_cols = ["Account Number", "CUSIP"]
        self.holdings_col_map = {
            "Account Number": "account",
            "CUSIP": "instrument",
            "Quantity": "custodian_units",
            "Account Currency": "currency",
            "Book Value Account Currency": "custodian_bv_ac_cad_usd",
            "Market Value Account Currency": "custodian_mv_clean_ac_cad_usd",
            "Last Price Security Currency": "custodian_price",
        }

    def clean_spaces_in_columns(self, df: pd.DataFrame, columns: list) -> pd.DataFrame:
        for col in columns:
            df[col].replace(" ", "", regex=True, inplace=True)

    def fill_cash_instruments_with_currency(self, df: pd.DataFrame) -> pd.DataFrame:
        mask = df["instrument"].isna() | (df["instrument"] == "")
        df.loc[mask, "instrument"] = df.loc[mask, "currency"]

    def set_djd_cash_price_and_units(self, df: pd.DataFrame) -> pd.DataFrame:
        mask = df["instrument"].isin(SUPPORTED_CURRENCIES)
        df.loc[mask, "custodian_units"] = df["custodian_mv_clean_ac_cad_usd"]
        df.loc[mask, "custodian_price"] = 1

    def read_holdings_file(self, desjardins_dte):
        file = f"{self.feed_path}/{desjardins_dte}/Holdings.txt"
        try:
            df = pd.read_csv(
                file,
                sep=";",
                skiprows=1,
                skipfooter=1,
                engine="python",
                names=self.djd_holdings_cols,
                dtype={x: str for x in self.holdings_str_cols},
            )
            return df.rename(columns=self.holdings_col_map)
        except FileNotFoundError:
            msg = f"Could not find Holdings file for {self.client} at {file}!"
            raise ClientDataNotFoundException(msg)

    def read_data(self, date: str) -> pd.DataFrame:
        recon_dte = dtU().get_recon_date(date)
        recon_dte += timedelta(days=1)
        desjardins_dte = dtU.get_custodian_date(recon_dte)
        holdings = self.read_holdings_file(desjardins_dte)
        holdings["date"] = pd.to_datetime(date)
        return holdings

    def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        columns_to_clean = ["instrument", "account"]
        self.clean_spaces_in_columns(df, columns_to_clean)
        self.fill_cash_instruments_with_currency(df)
        self.set_djd_cash_price_and_units(df)
        res = df[self.custodian_return_cols]
        return res.groupby(["account", "instrument", "date"]).first().reset_index()

    def get_custdn_data(self, dte) -> pd.DataFrame:
        df = self.read_data(dte)
        res = self.process_data(df)
        return res
