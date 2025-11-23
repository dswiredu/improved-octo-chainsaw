import os
from typing import List

from dagster import asset, AssetsDefinition, AssetKey
from dagster_etl.partitions import RAW_DATES
from pandas import DataFrame

from utils.config import get_asset_manager_config
from importer.extractor import Extractor
from connectors.mysql_connector import MySQLDataSource

from dagster import AutoMaterializePolicy

# ─── load AM config once ───────────────────────────────────────────────
_ETL_LOC = os.getenv("ETL_LOC")
_AM_CONFIG = get_asset_manager_config(_ETL_LOC)
RAW_AM_NAMES = set(_AM_CONFIG.keys())  # exported for bronze_factory


def _make_raw_asset(am_name: str, am_cfg: dict) -> AssetsDefinition:
    """Return one Dagster asset ["raw", <am_name>] with deep lineage."""
    asset_key = AssetKey(["raw", am_name])

    @asset(
        name=am_name,  # row label “26n”, “himco”, …
        key_prefix=["raw"],  # full key ["raw", am_name]
        partitions_def=RAW_DATES,
        io_manager_key="noop_io",
        auto_materialize_policy=AutoMaterializePolicy.eager(),
        description=f"Raw {am_name.upper()} positions",
        group_name="RawData",
        tags={
            "engine": "pandas",
            "source": "sftp",
            "owner": "dwiredu",
            "domain": "finance",
            "sensitivity": "pii",
            "client": am_name,  # if dynamic per asset
        },
        metadata={"author": "david", "purpose": "raw ingest"},
        compute_kind="pandas + mysql",
        code_version="v1.0.0",
    )
    def _raw(context) -> DataFrame:
        date = context.partition_key
        extractor = Extractor(MySQLDataSource, am_name, am_cfg)

        # run extractor → (df, tracker, [source_files])
        df, tracker, src_files = extractor.run_with_lineage(date)

        # column-level lineage (Dagster ≥ 1.5 draws arrows automatically)
        _raw.column_lineage = tracker.to_dagster()

        # attach metadata for file-level lineage & schema introspection
        context.add_output_metadata(
            {
                "rows": len(df),
                "source_files": src_files,
                "column_lineage": _raw.column_lineage,  # stored for <1.5 too
            }
        )
        return df

    return _raw


# ─── generate one raw asset per entry in JSON config ───────────────────
raw_assets: List[AssetsDefinition] = [
    _make_raw_asset(name, cfg) for name, cfg in _AM_CONFIG.items()
]
