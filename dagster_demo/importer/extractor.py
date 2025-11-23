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


class Extractor:
    def __init__(self, datasource: Any, name: str, asset_manager_config: dict) -> None:
        self.name = name
        self.datasource = datasource
        self.asset_manager_config = asset_manager_config
        self.feed_path = asset_manager_config.get("feed_path")
        self.dbname = asset_manager_config["dbname"]
        self.table_name = f"positions_{name}_test"

    def initialize_datasrc(self) -> Any:
        ds = self.datasource(
            dbname=self.dbname,
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=int(os.getenv("DB_PORT")),
        )
        return ds

    @property
    def _cls_name(self) -> str:
        """Returns the class name for an asset manager."""
        return f"AM{self.name.upper()}"

    def save_manager_data(self, df: pd.DataFrame) -> None:
        LOG.info(f"Initializing datasource for {self.name}...")
        ds = self.initialize_datasrc()
        LOG.info(f"Writing {len(df)} rows to {self.dbname}...")
        ds.write_table(
            df,
            table_name=self.table_name,
        )
        LOG.info("Finished writing data....")

    def run(self, dte: str) -> pd.DataFrame:
        cls = getattr(am, self._cls_name)
        manager = cls(self.name, self.feed_path)
        LOG.info(f"Retrieving asset manager data for {self.name}")
        df = manager.get_asset_manager_data(dte)
        self.save_manager_data(df)
        return df

    def run_with_lineage(
        self, dte: str
    ) -> tuple[pd.DataFrame, LineageTracker, list[str]]:
        """
        Wrapper used by Dagster raw assets.
        Returns (df, tracker, source_files).
        """
        cls = getattr(am, self._cls_name)
        manager = cls(self.name, self.feed_path)

        df, tracker, files = manager.get_df_with_lineage(
            dte, AssetKey(["raw", self.name])
        )

        self.save_manager_data(df)
        return df, tracker, files
