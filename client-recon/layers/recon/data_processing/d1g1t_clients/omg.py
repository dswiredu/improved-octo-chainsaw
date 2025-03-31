import logging
import pandas as pd
from layers.recon.data_processing.d1g1t_clients.d1g1t_client import D1g1tClient
from layers.recon.exceptions import (
    ClientDataNotFoundException,
)

logger = logging.getLogger(__name__)


class Omg(D1g1tClient):
    def __init__(self, firm: str, client: str) -> None:
        super().__init__(firm, client)
        self.omg_bv_cols_map = {
            "TI Alternate ID": "instrument",
            "A/C ID": "account",
            "B/V Security Position Val": "custodian_bv_ac_cad_usd",
        }

    def apply_firm_specific_d1g1t_logic(self, d1g1t_df: pd.DataFrame) -> pd.DataFrame:
        return d1g1t_df

    def apply_firm_specific_custodian_logic(
        self, custodian: str, custodian_df: pd.DataFrame
    ) -> pd.DataFrame:
        if custodian == "nbin":
            date = custodian_df["date"].dt.strftime("%y%m%d").iloc[0]
            try:
                omg_bv_data = self.read_omg_bv_data(date)
                merge_cols = ["account", "instrument"]
                res = pd.merge(
                    custodian_df, omg_bv_data, how="left", on=merge_cols, validate="1:1"
                )
                return res
            except Exception as e:
                msg = f"failed to get omg client bv data due to error: {e}"
                logger.info(msg)
                return custodian_df

    def apply_recon_post_processing_logic(self, df: pd.DataFrame) -> pd.DataFrame:
        return df

    def omg_bv_file_path(self, omg_dte):
        file = f"s3://d1g1t-production-file-transfer-ca-central-1/omg/omg/BVdata/OMGWMPOS{omg_dte}01.CSV"
        return file

    def read_omg_bv_data(self, omg_dte):
        s3_omg_file = self.omg_bv_file_path(omg_dte)
        try:
            df = pd.read_csv(s3_omg_file, usecols=self.omg_bv_cols_map.keys())
        except FileNotFoundError:
            msg = f"No data found for {self.client} at {s3_omg_file}!"
            raise ClientDataNotFoundException(msg)
        df.rename(columns=self.omg_bv_cols_map, inplace=True)
        df["instrument"] = df["instrument"].astype(str).str.strip()
        df["account"] = df["account"].astype(str).str.strip()
        df = df[df["instrument"] != ""]
        return df
