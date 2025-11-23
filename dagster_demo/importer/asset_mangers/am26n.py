import pandas as pd
import glob, os

import logging
from datetime import datetime

from importer.asset_mangers.asset_manager import AssetManager

LOG = logging.getLogger(__name__)


class AM26N(AssetManager):
    def __init__(self, name, feed_path) -> None:
        super().__init__(name, feed_path)

        self.read_cols = [
            "POS_DATE",
            "CUSIP",
            "PORTFOLIO",
            "Purchase Price",
            "MKT_VALUE_FLAT",
            "ISIN",
            "COUPON",
        ]

        self.rename_cols = {
            "POS_DATE": "date",
            "CUSIP": "instrument",
            "Portfolio": "account",
            "MKT_VALUE_FLAT": "amount",
            "COUPON": "coupon",
        }

        self.num_cols = ["Purchase Price", "amount"]

        self.manager_return_cols = [
            "date",
            "account",
            "instrument",
            "coupon",
            "amount",
            "qty",
            "ISIN",
        ]

    def get_feed_file(self, dte: str) -> str:
        am_dte = datetime.strptime(dte, "%Y-%m-%d").strftime("%Y%m%d")
        files = glob.glob(os.path.join(self.feed_path, f"Analytics_{am_dte}.csv"))

        if not files:
            return None

        for f in files:
            if "revised" in os.path.basename(f).lower():
                return f

        # Else return the normal one
        return files[0]

    def read_data(self, dte) -> pd.DataFrame:
        file = self.get_feed_file(dte)
        df = pd.read_csv(file, dtype=str, usecols=self.read_cols)
        return df.rename(columns=self.rename_cols)

    def convert_file_dates(dates: pd.Series) -> pd.Series:
        fdate = pd.to_datetime(dates, format="%m/%d/%Y")
        return fdate.dt.strftime("%Y-%m-%d")

    def get_quantity(df: pd.DataFrame) -> pd.Series:
        price, mv = df["price"], df["amount"]
        res = mv.divide(price)
        return res.fillna(1)

    def process_data(self, df) -> pd.DataFrame:
        df[self.num_cols] = df[self.num_cols].astype(float)
        df["date"] = self.convert_file_dates(df["date"])
        df["qty"] = self.get_quantity(df)
        df.rename(columns=self.rename_cols, inplace=True)
        return df[self.manager_return_cols]

    # def get_asset_manager_data(self, dte) -> pd.DataFrame:
    #     df = self.read_data(dte)
    #     res = self.process_data(df)
    #     return res[self.manager_return_cols]
