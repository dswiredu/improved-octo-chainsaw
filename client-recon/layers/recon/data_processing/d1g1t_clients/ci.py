import pandas as pd
import logging

from layers.recon.data_processing.d1g1t_clients.d1g1t_client import D1g1tClient
from layers.recon.data_processing.lookup import CCY_MAP

logger = logging.getLogger(__name__)


class Ci(D1g1tClient):
    def __init__(self, firm: str, client: str) -> None:
        super().__init__(firm, client)

    def ci_recon_columns(self):
        column_file = "s3://d1g1t-client-ca/ci/recon/ci-recon-columns.csv"
        df = pd.read_csv(column_file, dtype=str, usecols=["columns"])
        return df["columns"].tolist()

    def apply_firm_specific_d1g1t_logic(self, d1g1t_df: pd.DataFrame) -> pd.DataFrame:
        d1g1t_df["account"] = d1g1t_df["account"].str.strip()
        d1g1t_df = d1g1t_df.drop_duplicates(subset=["date", "account", "instrument"])
        d1g1t_df["d1g1t_ai"] = d1g1t_df["d1g1t_ai"].fillna(0)
        return d1g1t_df

    def apply_firm_specific_custodian_logic(
        self, custodian: str, custodian_df: pd.DataFrame
    ) -> pd.DataFrame:
        return custodian_df

    @staticmethod
    def override_cash_recon(df: pd.DataFrame) -> None:
        suffix = "_reconciled"
        client_cash_threshold = 5
        diffs = df.filter(like=suffix)
        metrics = [x.split(suffix)[0] for x in diffs.columns]
        cash_idx = df["instrument"].isin(CCY_MAP.values())
        for metric in metrics:
            cash_reconciled = df[f"{metric}_diff"].abs() <= client_cash_threshold
            df.loc[cash_idx, f"{metric}{suffix}"] = cash_reconciled

    def make_diff_columns_absolute(self, df: pd.DataFrame) -> None:
        diffs = df.filter(like="diff")
        for metric in diffs.columns:
            df[f"{metric}"] = df[f"{metric}"].abs()

    def create_acct_mv_percentage(self, df: pd.DataFrame) -> None:
        df["%AcctMV"] = ""
        mv_dirty_diff_0_idx = df["mv_dirty_diff"] == 0
        df.loc[mv_dirty_diff_0_idx, "%AcctMV"] = 0
        custodian_mv_dirty_0_idx = df["custodian_mv_dirty"] == 0
        df.loc[custodian_mv_dirty_0_idx, "%AcctMV"] = 100
        acct_mv_0_idx = df["%AcctMV"] == ""
        df.loc[acct_mv_0_idx, "%AcctMV"] = (
            (df["mv_dirty_diff"] / df["custodian_mv_dirty"].abs()) * 100
        ).round(4)

    def apply_recon_post_processing_logic(self, df: pd.DataFrame) -> pd.DataFrame:
        self.override_cash_recon(df)
        self.make_diff_columns_absolute(df)
        self.create_acct_mv_percentage(df)
        return df[self.ci_recon_columns()]
