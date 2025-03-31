import pandas as pd
import logging
import requests

from layers.common.connections.connections import Connection
from layers.recon.data_processing.custodians.custodian import Custodian
from layers.recon.datehandler import DateUtils as dtU
from layers.recon.exceptions import (
    ClientDataNotFoundException,
    FirmNotConfiguredException,
)

logger = logging.getLogger(__name__)


class SGGG(Custodian):
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
        self.fund_map_loc = "s3://d1g1t-client-ca/sggg_validation"  # TODO: Switch to point to client properties
        self.fund_file = f"{self.fund_map_loc}/{self.firm}.csv"
        self.sggg_url = "https://api.sgggfsi.com/api/v1"
        self.fundid_map = self.get_client_fund_map()

    @property
    def sggg_login_url(self) -> str:
        return f"{self.sggg_url}/login/"

    @property
    def account_positions_endpoint(self) -> str:
        return f"{self.sggg_url}/Accounts/GetAccountPositions/"

    @property
    def secret_id(self) -> str:
        return f"production/{self.firm}"

    def get_login_details(self) -> dict:
        try:
            logger.info(f"Retrieving {self.firm} secrets...")
            conn = Connection(self.secret_id)
            secrets = conn.get_connection()
            username = secrets["custodian_username"]
            password = secrets["custodian_password"]
            return {"Username": username, "Password": password}
        except Exception:
            msg = f"Retrieval failed! Please ensure secrets exist for secret_id: {self.secret_id}!"
            raise FirmNotConfiguredException(msg)

    def login(self):
        login_info = self.get_login_details()

        logger.info("Logging into sggg api...")
        session = requests.session()
        response_auth = session.post(self.sggg_login_url, json=login_info, verify=False)
        if response_auth.status_code == 200:
            logger.info("Successfully logged in to sggg api!")
            auth_key = response_auth.json()["AuthKey"]
            headers = {"Authorization": f"AuthKey {auth_key}"}
            return session, headers
        else:
            msg = "Log in attempt was unsuccsessful!"
            raise FirmNotConfiguredException(msg)

    def get_client_fund_map(self) -> dict:
        """Each client will pull a specifc set of fund Ids from
        a csv file that has sggg-to-d1g1t fund id
        """
        try:
            mapp = pd.read_csv(self.fund_file, index_col="FundID", dtype=str)
            return self.fund_map_to_dict(mapp)
        except FileNotFoundError:
            msg = f"FundID map not found for client {self.firm} at {self.fund_file}!"
            raise FirmNotConfiguredException(msg)

    @staticmethod
    def fund_map_to_dict(df: pd.DataFrame) -> dict:
        return df.to_dict()["instrument"]

    @staticmethod
    def sggg_response_to_df(response: dict) -> pd.DataFrame:
        """
        Parse sggg Fund accounts response into a dataframe containing
        fundpositions

        :param: reponse: dictionary with key "Accounts" containing
        """
        data: list = response["Accounts"]
        df = pd.json_normalize(data, "FundPositions")
        return_cols = ["AccountID", "FundID", "TotalUnits", "MarketValue"]
        return df[return_cols]

    def read_data(self, date: str) -> pd.DataFrame:
        recon_dte = dtU().get_recon_date(date)
        sggg_dte = dtU.get_custodian_date(recon_dte)
        accs_pos_data = {"HistoricalDate": sggg_dte, "DateType": "T"}
        session, headers = self.login()
        response = session.post(
            self.account_positions_endpoint,
            json=accs_pos_data,
            headers=headers,
        )
        if response.status_code == 200:
            df = self.sggg_response_to_df(response.json())
            df["date"] = pd.to_datetime(sggg_dte)
            return df
        else:
            msg = f"Could not retrieve account positions for {self.firm}"
            raise ClientDataNotFoundException(msg)

    def map_d1g1t_fund_ids(self, df: pd.DataFrame) -> pd.Series:
        res = df["FundID"].copy()
        return res.map(self.fundid_map)

    def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        rename_cols = {
            "AccountID": "account",
            "TotalUnits": "custodian_units",
            "MarketValue": "custodian_mv_dirty",
        }
        df["instrument"] = self.map_d1g1t_fund_ids(df)
        df.rename(columns=rename_cols, inplace=True)
        return df[self.custodian_return_cols]

    def get_custdn_data(self, dte) -> pd.DataFrame:
        df = self.read_data(dte)
        res = self.process_data(df)
        return res
