import pandas as pd

from layers.recon.data_processing.d1g1t_clients.d1g1t_client import D1g1tClient
from layers.recon.data_processing.d1g1t import read_d1g1t_data


class Claret(D1g1tClient):
    def __init__(self, firm: str, client: str) -> None:
        super().__init__(firm, client)
        self.client_loc = "s3://d1g1t-custodian-data-ca-central-1/apx"

        self.client_filemap = {
            "security": {
                "file": f"{self.client_loc}/{self.firm}/YYYYMMDD/Security.csv",
                "usecols": ["SecurityID", "SecurityTypeCode", "Symbol"],
                "rename_col_map": {
                    "SecurityID": "instrument",
                    "SecurityTypeCode": "SecTypeCode",
                },
            }
        }

    @property
    def recon_columns(self):
        column_file = (
            "s3://d1g1t-client-ca/claret/daily-reconciliation/claret-recon-columns.csv"
        )
        df = pd.read_csv(column_file, dtype=str, usecols=["columns"])
        return df["columns"].tolist()

    def get_client_raw_data(self, file_type: str, apx_dte: str):
        file_info = self.client_filemap[file_type]
        data_file = file_info["file"].replace("YYYYMMDD", apx_dte)
        usecols = file_info.get("usecols")
        rename_map = file_info.get("rename_col_map")
        res = pd.read_csv(data_file, usecols=usecols, dtype=str)
        return res.rename(columns=rename_map)

    def get_recon_with_client_properties_attached(
        self, apx_dte, df: pd.DataFrame
    ) -> pd.DataFrame:
        d1g1t_dte = apx_dte.strftime("%Y-%m-%d")
        client_dte = apx_dte.strftime("%Y%m%d")
        accounts = read_d1g1t_data(
            self.firm, self.client, "production", "accounts", d1g1t_dte
        )
        accounts = accounts[
            ["account", "account_user_defined_1", "account_start_date"]
        ].rename(
            columns={
                "account": "account",
                "account_user_defined_1": "AxysCode",
                "account_start_date": "account_open_date",
            }
        )
        security = self.get_client_raw_data("security", client_dte)
        account_recon = df.merge(accounts, on=["account"], how="left", validate="m:1")
        res = account_recon.merge(
            security, on=["instrument"], how="left", validate="m:1"
        )
        return res

    @staticmethod
    def update_missing_security_fields(df: pd.DataFrame) -> None:
        cash_sectype = "ca" + df["instrument"].str[:2].str.lower()
        df["SecTypeCode"].fillna(cash_sectype, inplace=True)
        df["Symbol"].fillna("cash", inplace=True)

    def apply_firm_specific_d1g1t_logic(self, d1g1t_df: pd.DataFrame) -> pd.DataFrame:
        return d1g1t_df

    def apply_firm_specific_custodian_logic(
        self, custodian: str, custodian_df: pd.DataFrame
    ) -> pd.DataFrame:
        return custodian_df

    def apply_recon_post_processing_logic(self, df: pd.DataFrame) -> pd.DataFrame:
        apx_dte = df["date"].iloc[0]
        res = self.get_recon_with_client_properties_attached(apx_dte, df)
        self.update_missing_security_fields(res)
        return res[self.recon_columns]
