import pandas as pd

from layers.recon.data_processing.d1g1t_clients.d1g1t_client import D1g1tClient


class Solidarity(D1g1tClient):
    def __init__(self, firm: str, client: str) -> None:
        super().__init__(firm, client)
        self.currency_mapper = {
            "USD999997": "USD",
        }

    def apply_pershing_logic(self, custodian_df: pd.DataFrame) -> None:
        custodian_df.replace({"instrument": self.currency_mapper}, inplace=True)
        custodian_df = custodian_df.groupby(
            ["account", "instrument", "date"], as_index=False
        ).agg({"custodian_units": sum})
        return custodian_df

    def apply_firm_specific_d1g1t_logic(self, d1g1t_df: pd.DataFrame) -> pd.DataFrame:
        return d1g1t_df

    def apply_firm_specific_custodian_logic(
        self, custodian: str, custodian_df: pd.DataFrame
    ) -> pd.DataFrame:
        if custodian == "pershing":
            custodian_df = self.apply_pershing_logic(custodian_df)
        return custodian_df

    def apply_recon_post_processing_logic(self, df: pd.DataFrame) -> pd.DataFrame:
        return df
