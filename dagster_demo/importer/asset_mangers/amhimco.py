import pandas as pd
import glob, os

import logging
from datetime import datetime

from importer.asset_mangers.asset_manager import AssetManager

LOG = logging.getLogger(__name__)


class AMHIMCO(AssetManager):
    def __init__(self, name, feed_path) -> None:
        super().__init__(name, feed_path)

        self.security_cols = [
            "CUSIP",
            "ISIN",
        ]

        self.position_rename_cols = {
            "POS_DATE": "date",
            "CUSIP": "instrument",
            "PORTFOLIO": "account",
            "MKT_VALUE_FLAT": "amount",
            "Purchase Price": "price",
        }

        self.num_cols = ["amount", "price"]

        self.prefix_map = {
            "security": "26N_AGAM_Out_125_DailySecurityMaster",
            "positions": "26N_AGAM_Out_DailyPositions",
        }

        self.return_cols = [
            "date",
            "account",
            "instrument",
            "amount",
            "price",
            "qty",
            "ISIN",
        ]

    def read_security_file(self, dte: str) -> pd.DataFrame:
        file = self.get_feed_file(dte, "security")
        try:
            df = pd.read_csv(file, dtype=str)
            return df
        except FileNotFoundError:
            LOG.exception("No data found...")

    def get_feed_file(self, dte: str, file_type: str) -> str:
        """
        Gets feed file for a given file type.
        """
        assert file_type in self.prefix_map.keys()
        am_dte = datetime.strptime(dte, "%Y-%m-%d").strftime("%Y%m%d")
        file_prefix = self.prefix_map[file_type]
        return os.path.join(self.feed_path, f"{file_prefix}_{am_dte}.csv")

    def read_data(self, dte, source_files: list[str]) -> pd.DataFrame:
        sec_file = self.get_feed_file(dte, file_type="security")
        posns_file = self.get_feed_file(dte, file_type="positions")

        source_files += [sec_file, posns_file]

        sec = pd.read_csv(sec_file, dtype=str, usecols=self.security_cols)
        posns = pd.read_csv(
            posns_file, dtype=str, usecols=list(self.position_rename_cols.keys())
        )
        df = posns.merge(sec, on="CUSIP", how="left")
        return df.rename(columns=self.position_rename_cols)

    @staticmethod
    def convert_file_dates(dates: pd.Series) -> pd.Series:
        fdate = pd.to_datetime(dates, format="%m/%d/%Y")
        return fdate.dt.strftime("%Y-%m-%d")

    @staticmethod
    def get_quantity(df: pd.DataFrame) -> pd.Series:
        price, mv = df["price"], df["amount"]
        res = mv.divide(price)
        return res.fillna(0)

    def process_data(self, df) -> pd.DataFrame:

        df[self.num_cols] = df[self.num_cols].astype(float)
        df["ISIN"].fillna("Unknown", inplace=True)

        df["date"] = self.convert_file_dates(df["date"])
        df["qty"] = self.get_quantity(df)
        return df[self.return_cols]

    # def get_asset_manager_data(self, dte) -> pd.DataFrame:
    #     df = self.read_data(dte)
    #     res = self.process_data(df)
    #     return res[self.return_cols]
