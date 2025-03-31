import pandas as pd

from layers.recon.data_processing.d1g1t_clients.d1g1t_client import D1g1tClient


class Lmcg(D1g1tClient):
    def __init__(self, firm: str, client: str) -> None:
        super().__init__(firm, client)

    def get_secmaster_file(self, apx_dte: str):
        return f"s3://d1g1t-custodian-data-us-east-1/apx/{self.firm}/{apx_dte}/Security.csv"

    @property
    def lmcg_recon_columns(self):
        column_file = (
            "s3://d1g1t-client-us/lmcg/daily-reconciliation/lmcg-recon-columns.csv"
        )
        df = pd.read_csv(column_file, dtype=str, usecols=["columns"])
        return df["columns"].tolist()

    @staticmethod
    def get_unsupervised_securities(df: pd.DataFrame) -> pd.DataFrame:
        res = df.copy()
        res["SecurityID"] = "unsup-" + res["SecurityID"]
        return res

    def get_lmcg_security_master(self, apx_dte: str):
        secmaster_file = self.get_secmaster_file(apx_dte)
        usecols = ["SecurityID", "SecurityTypeCode", "Symbol"]
        sec = pd.read_csv(secmaster_file, usecols=usecols, dtype=str)
        unsup_sec = self.get_unsupervised_securities(sec)
        res = pd.concat([sec, unsup_sec], ignore_index=True)
        return res.rename(
            columns={"SecurityID": "instrument", "SecurityTypeCode": "SecTypeCode"}
        )

    def apply_firm_specific_d1g1t_logic(self, d1g1t_df: pd.DataFrame) -> pd.DataFrame:
        return d1g1t_df

    def apply_firm_specific_custodian_logic(
        self, custodian: str, custodian_df: pd.DataFrame
    ) -> pd.DataFrame:
        unsupervised_idx = custodian_df["SecTypeCode"].str.startswith("u")
        custodian_df["instrument"].loc[unsupervised_idx] = (
            "unsup-" + custodian_df["instrument"]
        )
        return custodian_df

    def apply_recon_post_processing_logic(self, df: pd.DataFrame) -> pd.DataFrame:
        apx_dte = df["date"].iloc[0].strftime("%Y%m%d")
        sec = self.get_lmcg_security_master(apx_dte)
        res = df.merge(sec, how="left", on=["instrument"], validate="m:1")
        res["SecTypeCode"].fillna("ca", inplace=True)
        res["Symbol"].fillna("cash", inplace=True)
        return res[self.lmcg_recon_columns]
