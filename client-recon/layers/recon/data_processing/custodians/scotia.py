import pandas as pd
import numpy as np
import logging

from layers.recon.data_processing.custodians.custodian import Custodian
from layers.recon.datehandler import DateUtils as dtU

logger = logging.getLogger(__name__)


class Scotia(Custodian):
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
        self.feed_path = self.get_feed_path

        self.position_file_str_col_map = {
            "holdings": ["account", "scotia_id", "cusip", "ticker", "isin"],
            "cash": ["account", "currency"],
        }

        self.holdings_fields = {
            "account": (0, 10),
            "scotia_id": (58, 65),
            "cusip": (65, 74),
            "ticker": (87, 94),
            "isin": (74, 86),
            "security_currency": (107, 108),
            "custodian_price": (167, 183),
            "custodian_units_settle": (183, 202),
            "custodian_bv_settle_CAD": (203, 221),
            "custodian_bv_settle_USD": (241, 259),
            "custodian_mv_clean_settle_CAD": (222, 240),
        }

        self.cash_fields = {
            "account": (0, 10),
            "currency": (50, 51),
            "custodian_units_settle": (100, 119),
        }

        self.currency_map = {"0": "CAD", "1": "USD"}
        self.position_file_map = {"holdings": "holdings", "cash": "Bdcbd3a.taaabdcd"}

    @property
    def output_path(self) -> str:
        region_map = {"ca": "central", "us": "east"}
        # hard coding for now.
        return f"s3://d1g1t-production-file-transfer-{self.region}-{region_map[self.region]}-1/{self.firm}/Validation"

    @property
    def get_feed_path(self) -> str:
        return f"s3://d1g1t-custodian-data-{self.region}-central-1/{self.custodian}/{self.feed}"

    def get_feed_file(self, file_date: str, filetype: str = "holdings") -> str:
        return f"{self.feed_path}/{file_date}/{self.position_file_map[filetype]}"

    def read_feed_file(self, s3_file: str, field_map: dict, filetype: str = "holdings"):
        str_cols = self.position_file_str_col_map[filetype]
        df = pd.read_fwf(
            s3_file,
            colspecs=list(field_map.values()),
            names=field_map.keys(),
            dtype={x: str for x in str_cols},
            skiprows=1,
            skipfooter=1,
        )
        return df

    def read_data(self, dte: str) -> pd.DataFrame:
        logger.info(
            f"Retrieving custodian data from {self.feed_path} for {self.firm}.."
        )

        recon_dte = dtU().get_recon_date(dte)
        scotia_dte = dtU.get_custodian_date(recon_dte)

        holdings_s3_file = self.get_feed_file(scotia_dte)
        holdings = self.read_feed_file(holdings_s3_file, self.holdings_fields)

        cash_s3_file = self.get_feed_file(scotia_dte, filetype="cash")
        cash = self.read_feed_file(cash_s3_file, self.cash_fields, filetype="cash")
        data = pd.concat([cash, holdings], ignore_index=True)
        data["date"] = pd.to_datetime(scotia_dte)
        return data

    def get_instrument(self, df: pd.DataFrame) -> pd.Series:
        """
        instrument is determined by the following order of priority for missing values:
        cusip -> ticker -> isin (without first two chars) -> scotia_id
        Remaining blanks are cash and filled with CAD or USD
        """
        instrument = (
            df["cusip"]
            .fillna(df["ticker"])
            .fillna(df["isin"].str[2:-1])
            .fillna(df["scotia_id"])
            .copy()
        )
        cash_instruments = df["currency"].map(self.currency_map)
        return instrument.fillna(cash_instruments)

    def aggregate_positions(self, df: pd.DataFrame) -> pd.DataFrame:
        posn_cols = ["date", "account", "instrument"]
        duplicates_idx = df.duplicated(subset=posn_cols, keep=False)
        if any(duplicates_idx):
            logger.warning(
                "Duplicates found in scotia positions files. Saving duplicates..."
            )
            duplicates = df[duplicates_idx]
            # Need to have these in a dated folder.
            duplicates.to_csv(
                f"{self.output_path}/scotia_duplicate_positions.csv", index=False
            )
            return df.groupby(posn_cols).sum().reset_index()
        else:
            return df

    @staticmethod
    def set_cash_values(df: pd.DataFrame) -> None:
        """
        Copy over cash units to cash market value and book value
        """
        cash_idx = df.instrument.isin(["CAD", "USD"])
        df.loc[cash_idx, "custodian_price"] = 1
        df.loc[cash_idx, "custodian_mv_clean_CAD"] = df["custodian_units_settle"]

    @staticmethod
    def get_custodian_book_values(df: pd.DataFrame, currency: str) -> None:
        if currency == "CAD":
            df["custodian_bv_settle_CAD"] = np.where(
                df.currency == "0",
                df.custodian_units_settle,
                df[f"custodian_bv_settle_{currency}"],
            )
            df["custodian_bv_settle_USD"] = np.where(
                df.instrument == "CAD", np.nan, df["custodian_bv_settle_USD"]
            )
            df["custodian_bv_settle_USD"] = np.where(
                df.security_currency.astype(int) == 0,
                np.nan,
                df["custodian_bv_settle_USD"],
            )
        elif currency == "USD":
            df["custodian_bv_settle_USD"] = np.where(
                df.currency == "1",
                df.custodian_units_settle,
                df[f"custodian_bv_settle_{currency}"],
            )
            df["custodian_bv_settle_CAD"] = np.where(
                df.instrument == "USD", np.nan, df["custodian_bv_settle_CAD"]
            )
            df["custodian_bv_settle_CAD"] = np.where(
                df.security_currency.astype(int) == 1,
                np.nan,
                df["custodian_bv_settle_CAD"],
            )

    def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df["instrument"] = self.get_instrument(df)
        wrong_cash_ids = [
            "0000000",
            "K269426",
        ]  # Wrong representation of CAD & USD in holdings. Per Grahame T!
        res_no_cash = df[~df.instrument.isin(wrong_cash_ids)]
        res = self.aggregate_positions(res_no_cash)
        self.set_cash_values(res)
        self.get_custodian_book_values(res, "CAD")
        self.get_custodian_book_values(res, "USD")
        return res[self.custodian_return_cols]

    def get_custdn_data(self, dte: str) -> pd.DataFrame:
        df = self.read_data(dte)
        res = self.process_data(df)
        return res
