import pandas as pd
import logging

from layers.recon.data_processing.custodians.custodian import Custodian
from layers.recon.datehandler import DateUtils
from layers.recon.exceptions import ClientDataNotFoundException

logger = logging.getLogger(__name__)


class RBCUHN(Custodian):
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
        self.custodian = "rbc-uhn"

        self.cols = {
            "POS": {
                0: "branch_cd",
                1: "account_cd",
                2: "type_account_cd",
                5: "security_adp_nbr",
                17: "custodian_units",
                22: "custodian_price",
                29: "custodian_mv_dirty",
                30: "custodian_bv",
            },
            "BAL": {
                **{0: "branch_cd", 1: "account_cd", 2: "security_adp_nbr"},
                **{(5 + i * 3): f"ydys_trade_dt_amt_type{i+1}" for i in range(9)},
            },
        }

        self.numeric_cols = [
            "custodian_units",
            "custodian_mv_dirty",
            "custodian_bv",
            "custodian_price",
        ]

    def get_feed_file(self, rbc_dte: str, file_name: str) -> str:
        file = f"{self.get_feed_path}/{rbc_dte}/{file_name}"
        return file

    def read_feed_file(
        self,
        rbc_dte: str,
        file_name: str,
    ) -> pd.DataFrame:
        s3_file = self.get_feed_file(rbc_dte, file_name)
        try:
            df = pd.read_csv(
                s3_file,
                dtype=str,
                skiprows=1,
                skipfooter=1,
                header=None,
                usecols=self.cols[file_name].keys(),
                sep="|",
            )
        except FileNotFoundError:
            # If client is not "august", raise the original FileNotFoundError
            msg = f"No data found for {self.firm} at {s3_file}!"
            raise ClientDataNotFoundException(msg)
        return df.rename(self.cols[file_name], axis=1)

    @staticmethod
    def process_instruments(df: pd.DataFrame) -> None:
        subs = {
            "001": "USD",
            "000": "CAD",
        }
        df["instrument"] = df["security_adp_nbr"]
        df["instrument"].replace(subs, inplace=True)

    def read_data(self, date: str) -> pd.DataFrame:
        today = DateUtils().get_recon_date(date)
        if self.firm == "august" and today.weekday() == 6:
            today = DateUtils.get_last_cob_date(today)
        previous_day = DateUtils.get_last_n_cob_date(today, n=1)
        rbc_dt = DateUtils.get_custodian_date(today)
        rbc_dt_m_one = DateUtils.get_custodian_date(previous_day)
        try:
            df_pos = self.read_feed_file(rbc_dt, "POS")
        except FileNotFoundError:
            if self.firm == "august":
                # If file not found and client is "august", try using the previous business day's date
                df_pos = self.read_feed_file(rbc_dt_m_one, "POS")
                msg = f"No POS file found for {self.firm} for this date {rbc_dt}!"
                raise ClientDataNotFoundException(msg)

        df_bal = self.read_feed_file(rbc_dt, "BAL")

        # get correct cash balance by account type
        df_bal = df_bal[df_bal["security_adp_nbr"] != "FE"]
        # get type from position file
        df_bal = df_bal.merge(
            df_pos[["branch_cd", "account_cd", "type_account_cd"]].drop_duplicates(),
            on=["branch_cd", "account_cd"],
            how="left",
        )
        df_bal["cash_col"] = "ydys_trade_dt_amt_type" + df_bal["type_account_cd"]
        df_bal["custodian_units"] = float("nan")

        value_cols = [col for col in df_bal.columns if col[:4] == "ydys"]
        for ind, row in df_bal.iterrows():
            if row["cash_col"] == row["cash_col"]:
                df_bal.loc[ind, "custodian_units"] = -pd.to_numeric(
                    row[row["cash_col"]]
                )
            else:
                values = row[value_cols][row != "0.00"]
                values = pd.to_numeric(values)
                df_bal.loc[ind, "custodian_units"] = (
                    -values.iloc[0] if len(values) > 0 else 0
                )
        df_bal["custodian_mv_dirty"] = df_bal["custodian_units"]

        df = pd.concat(
            [
                df_pos,
                df_bal[
                    [
                        "branch_cd",
                        "account_cd",
                        "security_adp_nbr",
                        "custodian_units",
                        "custodian_mv_dirty",
                    ]
                ],
            ]
        )
        df["date"] = pd.to_datetime(date)
        return df

    def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        df["account"] = df["branch_cd"] + df["account_cd"]
        self.process_instruments(df)
        for col in self.numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        # aggregate df
        # TODO: convert mvs to security currency
        aggregated_df = (
            df.groupby(["account", "instrument", "date"]).sum().reset_index()
        )
        return aggregated_df[self.custodian_return_cols]

    def get_custdn_data(self, dte) -> pd.DataFrame:
        df = self.read_data(dte)
        res = self.process_data(df)
        return res
