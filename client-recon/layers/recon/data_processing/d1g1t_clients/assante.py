import pandas as pd
import logging

from layers.recon.data_processing.d1g1t_clients.d1g1t_client import D1g1tClient
from layers.recon.validation import override_cash_recon_by_threshold


logger = logging.getLogger(__name__)


class Assante(D1g1tClient):
    def __init__(self, firm: str, client: str) -> None:
        super().__init__(firm, client)
        self.position_cols = ["date", "account", "instrument"]
        self.d1g1t_str_cols = [
            "account",
            "instrument",
            "instrument_name",
            "account_name",
            "account_currency",
            "custodian",
        ]
        self.d1g1t_dates_cols = ["start_date", "date"]
        self.d1g1t_ext_cols = ["d1g1t_units", "d1g1t_price", "d1g1t_mv", "d1g1t_ai"]
        self.d1g1t_use_cols = [
            "date",
            "custodian",
            "account",
            "account_name",
            "account_currency",
            "instrument",
            "instrument_name",
            "d1g1t_units",
            "d1g1t_price",
            "d1g1t_mv_dirty",
            "d1g1t_ai",
        ]

    def get_ci_instrument(self, d1g1t_df: pd.DataFrame) -> pd.DataFrame:
        res = d1g1t_df["instrument"].astype(str)
        big_sec_idx = res.str.len() == 14
        res.loc[big_sec_idx] = res.str[:7]
        return res

    def get_ci_is_dead(self, d1g1t_df: pd.DataFrame) -> pd.DataFrame:
        res = d1g1t_df["is_dead"]
        is_dead_idx = res == "TRUE"
        res.loc[is_dead_idx] = "t"
        res.loc[~is_dead_idx] = "f"
        return res

    def get_ci_ai(self, d1g1t_df: pd.DataFrame) -> pd.DataFrame:
        res = d1g1t_df["d1g1t_ai"]
        ai_zero_idx = res == 0
        res.loc[ai_zero_idx] = ""
        return res

    def get_flag_for_positions_with_pending_trades(self, d1g1t_df: pd.DataFrame):
        date = d1g1t_df["date"][0].strftime("%Y-%m-%d")
        pending_trades_file = (
            f"s3://d1g1t-client-ca-central-1/assante/exports/recon/pending_trade_positions/"
            f"production/assante_{date}.csv"
        )
        try:
            df = pd.read_csv(pending_trades_file, dtype=str)
            df.columns = ["account", "instrument"]
            df["Pending_Trades"] = "Yes"
            merged_df = pd.merge(d1g1t_df, df, on=["account", "instrument"], how="left")
            merged_df["Pending_Trades"].fillna("No", inplace=True)
            return merged_df
        except FileNotFoundError:
            logger.warning("Could not find pending trade positions file for assante!")
            return d1g1t_df

    def assante_recon_columns(self):
        column_file = "s3://d1g1t-client-ca/assante/recon/assante-recon-columns.csv"
        df = pd.read_csv(column_file, dtype=str, usecols=["columns"])
        return df["columns"].tolist()

    def update_ci_currency_columns(self, d1g1t_df: pd.DataFrame) -> pd.DataFrame:
        currency_idx = d1g1t_df["instrument"].isin(["CAD", "USD"])
        d1g1t_df.loc[currency_idx, "d1g1t_price"] = 1
        d1g1t_df.loc[currency_idx, "d1g1t_mv_dirty"] = d1g1t_df["d1g1t_units"]
        return d1g1t_df

    def apply_firm_specific_d1g1t_logic(self, d1g1t_df: pd.DataFrame) -> pd.DataFrame:
        d1g1t_df["instrument"] = self.get_ci_instrument(d1g1t_df)
        d1g1t_df.fillna(0, inplace=True)
        d1g1t_df["is_dead"] = self.get_ci_is_dead(d1g1t_df)
        d1g1t_df["d1g1t_ai"] = self.get_ci_ai(d1g1t_df)
        d1g1t_df = d1g1t_df[self.d1g1t_use_cols]

        d1g1t_df = (
            d1g1t_df.groupby(
                ["date", "account", "instrument", "custodian", "account_currency"]
            )
            .sum()
            .reset_index()
        )

        d1g1t_df = self.update_ci_currency_columns(d1g1t_df)

        d1g1t_df.d1g1t_units = d1g1t_df.d1g1t_units.round(6)
        d1g1t_df = d1g1t_df.loc[d1g1t_df.d1g1t_units != 0]
        d1g1t_df.d1g1t_mv_dirty = d1g1t_df.d1g1t_mv_dirty.round(2)
        return d1g1t_df

    def apply_firm_specific_custodian_logic(
        self, custodian: str, custodian_df: pd.DataFrame
    ) -> pd.DataFrame:
        return custodian_df

    def apply_recon_post_processing_logic(self, df: pd.DataFrame) -> pd.DataFrame:
        override_cash_recon_by_threshold(df, 5)
        df["Instrument ID"] = df["instrument"]
        numeric_columns = df.columns[df.dtypes == "float64"].tolist()
        df[numeric_columns] = df[numeric_columns].round(4)
        res = self.get_flag_for_positions_with_pending_trades(df)
        return res[self.assante_recon_columns()]
