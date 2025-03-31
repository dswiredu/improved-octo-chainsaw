import pandas as pd

from layers.recon.data_processing.d1g1t_clients.d1g1t_client import D1g1tClient
from layers.recon.data_processing.lookup import CCY_MAP


class Ldic(D1g1tClient):
    def __init__(self, firm: str, client: str) -> None:
        super().__init__(firm, client)

    def apply_firm_specific_d1g1t_logic(self, d1g1t_df: pd.DataFrame) -> pd.DataFrame:
        return d1g1t_df

    def apply_firm_specific_custodian_logic(
        self, custodian: str, custodian_df: pd.DataFrame
    ) -> pd.DataFrame:
        if custodian == "bmo":
            self.apply_bmo_logic(custodian_df)
        return custodian_df

    @staticmethod
    def apply_bmo_logic(custodian_df: pd.DataFrame) -> None:
        custodian_df["account"] = (
            custodian_df["account"]
            + custodian_df["account_type_code"]
            + custodian_df["account_check_d1g1t"]
            + custodian_df["account_fund_portfolio_currency"].str[:1]
        )

    def apply_recon_post_processing_logic(self, df: pd.DataFrame) -> pd.DataFrame:
        cash_idx = df["instrument"].isin(CCY_MAP.values())
        bmo_idx = df["custodian"] == "BMO"
        replace_idx = cash_idx & bmo_idx
        bv_columns = ["bv_CAD", "bv_USD"]
        for col in bv_columns:
            df.loc[replace_idx, f"{col}_reconciled"] = True
            df.loc[replace_idx, "Note"] = "BMO does not provide correct BVs for cash."
        return df
