import pandas as pd
import logging

from layers.recon.data_processing.custodians.custodian import Custodian
from layers.recon.datehandler import DateUtils
from layers.recon.exceptions import ClientDataNotFoundException

logger = logging.getLogger(__name__)


class PCR(Custodian):
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
        self.pcr_cols = [
            "Unique_Account_ID",
            "Security_SID",
            "Position_Quantity",
            "Position_Value",
            "Position_Cost",
            "Position_Date",
            "Position_Price",
            "Institution_Type",
        ]

        self.numeric_cols = [
            "custodian_units",
            "custodian_mv_clean_USD",
            "custodian_bv",
            "custodian_price",
        ]

    def get_feed_file(self, pcr_dte):
        file = f"{self.feed_path}/{pcr_dte}/HOLDING_recon.csv"
        return file

    @staticmethod
    def process_instruments(df: pd.DataFrame) -> None:
        subs = {"pcr_234756": "USD", "pcr_466980": "CAD", "pcr_285621": "CAD"}
        df["instrument"] = "pcr_" + df["Security_SID"]
        df["instrument"].replace(subs, inplace=True)

    def up_to_date_price(self, df: pd.DataFrame) -> pd.DataFrame:
        df_clean_data = df.drop(["Position_Price"], axis=1)
        df_latest_price = df[["Security_SID", "Position_Date", "Position_Price"]]
        df_latest_price["index"] = range(len(df_latest_price))
        df_latest_price = df_latest_price.sort_values(
            by=["Position_Date", "index"], ascending=[False, False]
        )
        df_latest_price.drop(["index", "Position_Date"], axis=1, inplace=True)
        df_latest_price = df_latest_price.drop_duplicates(
            subset="Security_SID", keep="first"
        ).reset_index(drop=True)
        df = df_clean_data.merge(df_latest_price, on="Security_SID", how="left")
        return df

    def read_data(self, date: str) -> pd.DataFrame:
        today = DateUtils().get_recon_date(date)

        pcr_dte = DateUtils.get_custodian_date(today)
        s3_file = self.get_feed_file(pcr_dte)
        try:
            df = pd.read_csv(s3_file, dtype=str, usecols=self.pcr_cols)
        except FileNotFoundError:
            msg = f"No data found for {self.firm} at {s3_file}!"
            raise ClientDataNotFoundException(msg)
        df["Position_Date"] = pd.to_datetime(df["Position_Date"])
        df["date"] = pd.to_datetime(pcr_dte)
        return df

    @staticmethod
    def get_holdings_excluding_alternative_duplicatess(
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Alternative instruments are sent with duplicate positions.
        Take position corresponding to the latest position_date
        """
        alt_idx = df["Institution_Type"] == "Alternative"
        if any(alt_idx):  # If there are any alternative duplicates
            all_alts = df[alt_idx]
            alt_pos_dates = all_alts.groupby(
                ["account", "instrument"]
            ).Position_Date.idxmax()
            alts = all_alts.loc[alt_pos_dates]
            brokerage = df[~alt_idx]
            res = pd.concat([alts, brokerage])
            return res
        else:
            return df

    @property
    def cust_return_cols(self):
        return self.custodian_return_cols + ["Position_Date"]

    def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self.up_to_date_price(df)
        df.rename(
            {
                "Unique_Account_ID": "account",
                "Position_Quantity": "custodian_units",
                "Position_Value": "custodian_mv_clean_USD",
                "Position_Cost": "custodian_bv",
                "Position_Price": "custodian_price",
            },
            axis=1,
            inplace=True,
        )
        self.process_instruments(df)
        for col in self.numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        # deal with pcr sending duplicates for alternatives
        df = self.get_holdings_excluding_alternative_duplicatess(df)
        # dealing with PCR sending old positions
        df = df.sort_values(by="Position_Date", ascending=False)
        df = df.groupby(["date", "account", "instrument"]).first().reset_index()
        df.loc[df["instrument"].isin(["CAD", "USD"]), "custodian_price"] = 1
        return df[self.cust_return_cols]

    def get_custdn_data(self, dte) -> pd.DataFrame:
        df = self.read_data(dte)
        processed_data = self.process_data(df)
        res = self.apply_firm_specific_logic(processed_data)
        return res[self.cust_return_cols]
