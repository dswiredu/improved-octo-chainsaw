import pandas as pd
import logging

from layers.recon.data_processing.custodians.custodian import Custodian
from layers.recon.datehandler import DateUtils
from layers.recon.exceptions import ClientDataNotFoundException

logger = logging.getLogger(__name__)


class InteractiveBrokers(Custodian):
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

        self.ib_cols_pos = [
            "Type",
            "AccountID",
            "ConID",
            "Currency",
            "Quantity",
            "MarketValue",
            "MarketPrice",
            "CostBasis",
            "AssetType",
            "FxRateToBase",
        ]

        self.ib_cols_pl = [
            "AccountID",
            "InternalAssetID",
            "Currency",
            "UnrealizedSTInBase",
        ]

        self.numeric_cols = {
            "custodian_units": "Quantity",
            "custodian_mv_clean": "MarketValue",
            "custodian_bv": "CostBasis",
            "custodian_price": "MarketPrice",
            "unrealized_gain": "UnrealizedSTInBase",
            "fx": "FxRateToBase",
        }

        self.cash_currencies = ["CAD", "USD"]

    @property
    def get_feed_path(self) -> str:
        return f"s3://d1g1t-custodian-data-{self.region}-central-1/{self.custodian}/{self.feed}"

    def get_feed_file(self, ib_dte: str, file_name: str) -> str:
        file = f"{self.feed_path}/{ib_dte}/{file_name}.csv"
        return file

    @staticmethod
    def get_instrument(df: pd.DataFrame) -> pd.Series:
        instrument = df["ConID"].copy()
        # ConID NAN refers to cash
        cash_ind = instrument.isna()
        instrument.loc[cash_ind] = df[cash_ind]["Currency"]
        instrument.loc[~cash_ind] = "ib_" + instrument[~cash_ind]
        return instrument

    def read_data(self, dte: str) -> pd.DataFrame:
        today = DateUtils().get_recon_date(dte)
        ib_dt = DateUtils.get_custodian_date(today)
        s3_file_pos = self.get_feed_file(ib_dt, "Position")
        s3_file_pl = self.get_feed_file(ib_dt, "PL")
        try:
            df_pos = pd.read_csv(s3_file_pos, usecols=self.ib_cols_pos, dtype=str)
        except FileNotFoundError:
            msg = f"No data found for {self.firm} at {s3_file_pos}!"
            raise ClientDataNotFoundException(msg)
        try:
            df_pl = pd.read_csv(s3_file_pl, usecols=self.ib_cols_pl, dtype=str)
        except FileNotFoundError:
            msg = f"No data found for {self.firm} at {s3_file_pl}!"
            raise ClientDataNotFoundException(msg)

        # drop taxlot rows from positions
        df_pos.drop(df_pos[df_pos["Type"] == "L"].index, inplace=True)
        # merge pnl and pos file
        df = df_pos.merge(
            df_pl,
            how="left",
            left_on=["AccountID", "ConID", "Currency"],
            right_on=["AccountID", "InternalAssetID", "Currency"],
        )

        df["date"] = pd.to_datetime(ib_dt)
        return df

    def process_data(self, df_in: pd.DataFrame) -> pd.DataFrame:
        df = df_in.copy()
        df.rename({"AccountID": "account"}, axis=1, inplace=True)
        df["instrument"] = self.get_instrument(df)
        for col, custodian_col in self.numeric_cols.items():
            df[col] = pd.to_numeric(df[custodian_col], errors="coerce")
        # drop accruals
        df = df[~df["AssetType"].isin(["INTACC", "DIVACC"])]
        # fx unrealized gain
        df["unrealized_gain_fxed"] = df["unrealized_gain"] / df["fx"]
        # adjust cash position for futures mtm
        futures_gains = df[df["AssetType"] == "FUT"][
            ["account", "Currency", "unrealized_gain"]
        ]
        futures_gains = (
            futures_gains.groupby(["account", "Currency"]).sum().reset_index()
        )
        futures_gains.rename({"unrealized_gain": "cash_adjust"}, axis=1, inplace=True)
        df = df.merge(futures_gains, how="left", on=["account", "Currency"])
        cash_ind = df["instrument"].str[:3] != "ib_"
        df.loc[cash_ind, "custodian_units"] = df["custodian_units"] - df[
            "cash_adjust"
        ].fillna(0)

        # replace futures mv with unrealized gains
        df.loc[df["AssetType"] == "FUT", "custodian_mv_clean"] = df["unrealized_gain"]
        # Compute the cash_idx once
        cash_idx = df["instrument"].isin(self.cash_currencies)
        df.loc[cash_idx, "custodian_price"] = 1
        df.loc[cash_idx, "custodian_mv_clean"] = df["custodian_units"]
        return df[self.custodian_return_cols]

    def get_custdn_data(self, dte) -> pd.DataFrame:
        df = self.read_data(dte)
        res = self.process_data(df)
        return res
