import logging
from typing import List, Tuple, Any
import warnings, os

import pandas as pd
from dotenv import load_dotenv
import connectors as conn
from importer import asset_mangers as am
from utils.exceptions import InputValidationException
from dagster import AssetKey
from utils.lineage_tracker import LineageTracker  # new import


LOG = logging.getLogger(__name__)

load_dotenv()


class BronzeAggregator:
    def __init__(
        self, datasource: Any, client: str, client_config: pd.DataFrame
    ) -> None:
        self.client = client
        self.datasource = datasource
        self.client_config = client_config
        self.asset_managers = set(client_config["asset_manager"])
        self.dbname = f"testdb"
        self.table_name = f"positions_bronze_{client}"
        self.portfolios = set(client_config["portfolio"])

    def initialize_datasrc(self) -> Any:
        ds = self.datasource(
            dbname=self.dbname,
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=int(os.getenv("DB_PORT")),
        )
        return ds

    def save_client_data(self, df: pd.DataFrame) -> None:
        LOG.info(f"Initializing datasource for {self.client}...")
        ds = self.initialize_datasrc()
        LOG.info(f"Writing {len(df)} rows to {self.dbname}...")
        ds.write_table(
            df,
            table_name=self.table_name,
        )
        LOG.info("Finished writing data....")

    def read_am_data(self, am: str, dte: str) -> pd.DataFrame:
        am_dbname = f"{am}riskdb"
        am_tablename = f"positions_{am}_test"
        ds = self.datasource(
            dbname=am_dbname,
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=int(os.getenv("DB_PORT")),
        )
        df = ds.read_table(table_name=am_tablename, filters={"date": ("date", dte)})
        return df

    def run(self, dte: str) -> pd.DataFrame:
        dfs = []
        for am in self.asset_managers:
            try:
                df = self.read_am_data(am, dte)
                dfs.append(df)
            except Exception as err:
                LOG.exception(f"Unexpected error {am} : {err}")
        if dfs:
            res = pd.concat(dfs, ignore_index=True)
            res = res[res["account"].isin(self.portfolios)]
            self.save_client_data(res)
            return res
        else:
            LOG.info(f"No data found for {self.client}")
