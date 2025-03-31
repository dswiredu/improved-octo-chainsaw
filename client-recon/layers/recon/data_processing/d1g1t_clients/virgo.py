import pandas as pd
import logging

from layers.recon.data_processing.d1g1t_clients.d1g1t_client import D1g1tClient

logger = logging.getLogger(__name__)


class Virgo(D1g1tClient):
    def __init__(self, firm: str, client: str) -> None:
        super().__init__(firm, client)

    def apply_firm_specific_d1g1t_logic(self, d1g1t_df: pd.DataFrame) -> pd.DataFrame:
        return d1g1t_df

    def apply_firm_specific_custodian_logic(
        self, custodian: str, custodian_df: pd.DataFrame
    ) -> pd.DataFrame:
        return custodian_df

    def apply_recon_post_processing_logic(self, df: pd.DataFrame) -> pd.DataFrame:
        s3_path = "s3://d1g1t-client-ca/virgo/recon/virgo_instrument_removal.csv"
        instrument_removal_list = pd.read_csv(s3_path)["instrument_id"].tolist()
        return df[~df["instrument"].astype(str).isin(instrument_removal_list)]
