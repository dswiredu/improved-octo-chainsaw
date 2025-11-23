# dagster_etl/defs/bronze_factory.py
"""
Bronze assets that automatically materialize the required raw-date
partition first.  Works out-of-the-box on Dagster 1.11.x.
"""

import os
from typing import List

import pandas as pd
from dagster import asset, AssetsDefinition, AssetKey, AssetIn

from dagster_etl.partitions import RAW_DATES
from utils.config import get_client_config
from dagster_etl.defs.raw_factory import RAW_AM_NAMES
from processing.bronze import BronzeAggregator
from connectors.mysql_connector import MySQLDataSource

# ─── Load client_config.csv once ──────────────────────────────────────
_ETL_LOC = os.getenv("ETL_LOC")
_CLIENT_DF = get_client_config(_ETL_LOC)


def _make_bronze(client: str, am_list: List[str]) -> AssetsDefinition:
    """Return one bronze asset with key ['bronze', <client>] partitioned by date."""

    am_list = [am for am in am_list if am in RAW_AM_NAMES]

    # Declare raw dependencies with unique keys
    ins = {
        f"raw_dep__{am}": AssetIn(key=AssetKey(["raw", am]))
        for am in am_list
    }

    @asset(
        name=client,
        key_prefix=["bronze"],
        partitions_def=RAW_DATES,
        io_manager_key="noop_io",
        ins=ins,
        description=f"Bronze positions aggregated for {client}",
        group_name="Bronze",
        tags={
            "engine": "pandas",
        }
    )
    def _bronze(context, **_) -> pd.DataFrame:  # 👈 safely absorb injected args
        date = context.partition_key
        client_cfg = _CLIENT_DF.query("client==@client")
        agg = BronzeAggregator(MySQLDataSource, client, client_cfg)
        bronze_df = agg.run(date)

        context.add_output_metadata({"rows": len(bronze_df)})
        return bronze_df

    return _bronze


# ─── Generate one bronze asset per client ─────────────────────────────
bronze_assets: List[AssetsDefinition] = [
    _make_bronze(client, grp["asset_manager"].unique().tolist())
    for client, grp in _CLIENT_DF.groupby("client")
]
