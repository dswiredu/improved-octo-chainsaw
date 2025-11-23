# dagster_etl/defs/silver_factory.py

import os
from typing import List

import pandas as pd
from dagster import asset, AssetsDefinition, AssetKey, AssetIn

from dagster_etl.partitions import RAW_DATES
from utils.config import get_client_config
from processing.silver import SilverAggregator
from connectors.mysql_connector import MySQLDataSource


_ETL_LOC = os.getenv("ETL_LOC")
_CLIENT_DF = get_client_config(_ETL_LOC)


def _make_silver(client: str) -> AssetsDefinition:
    """Return one silver asset with key ['silver', <client>] partitioned by date."""

    @asset(
        name=client,
        key_prefix=["silver"],
        partitions_def=RAW_DATES,
        io_manager_key="noop_io",
        ins={"bronze_data": AssetIn(key=AssetKey(["bronze", client]))},  # just this!
        description=f"Client-specific silver positions for {client}",
        group_name="Silver",
        tags={
            "engine": "pandas",
        }
    )
    def _silver(context, bronze_data: pd.DataFrame) -> pd.DataFrame:
        date = context.partition_key
        client_cfg = _CLIENT_DF.query("client==@client")
        agg = SilverAggregator(MySQLDataSource, client, client_cfg)

        silver_df = agg.run(date)
        context.add_output_metadata({"rows": len(silver_df)})

        return silver_df

    return _silver


# ─── generate one silver asset per client ─────────────────────────────
silver_assets: List[AssetsDefinition] = [
    _make_silver(client) for client in _CLIENT_DF["client"].unique()
]
