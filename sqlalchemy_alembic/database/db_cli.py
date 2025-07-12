import os
import click
import pandas as pd
from pathlib import Path
from typing import List

from sqlalchemy import create_engine
from sqlalchemy_utils import (
    database_exists,
    create_database,
)  # pip install sqlalchemy-utils

import connectors as conn
from database.models import common, asset_manager  # registers models
from database.base import Base

from dotenv import load_dotenv
import os

load_dotenv()


def _engine(db_name: str):
    """
    Helper: builds a SQLAlchemy Engine via your existing connector
    """
    cls_name = os.getenv("DB_DRIVER_KEY", "MySQLDataSource")
    try:
        ds_cls = getattr(conn, cls_name)
    except AttributeError:
        raise click.ClickException(f"Unsupported DB_DRIVER_KEY='{cls_name}'. ")

    ds = ds_cls(
        dbname=db_name,
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        port=int(os.getenv("DB_PORT")),
    )

    if not database_exists(ds.dsn):
        create_database(ds.dsn)

    return ds._engine


@click.group(help="Database-related commands")
@click.pass_context
def db(ctx) -> None:
    """
    All DB sub-commands live here.
    Run `python -m etl db <subcommand>`
    ctx.obj['client_map'] is provided by etl/etl.py.
    """
    ctx.ensure_object(dict)


@db.command("build-tables")
@click.option("--client", "-c", required=True, metavar="<CLIENT>")
@click.pass_context
def build_tables(ctx, client: str):
    """
    Creates lookup DB + asset-manager RDBs for <client>.
    Expects ctx.obj["client_map"] to contain the mapping.
    """
    client = client.lower()
    client_map: dict[str, List[str]] = ctx.obj.get("client_map", {})

    if client not in client_map:
        raise click.BadParameter(
            f"Unknown client '{client}'. " f"Available: {list(client_map)}"
        )

    am_codes = client_map[client]
    engine = _engine(f"{client}rdb")

    client_tbls = [
        t for t in Base.metadata.sorted_tables if t.name != "positions_bronze"
    ]  # This might become a list later.
    Base.metadata.create_all(engine, tables=client_tbls)

    for am in am_codes:
        am_engine = _engine(f"{am}rdb")
        bronze = Base.metadata.tables["position_bronze"]
        raw = Base.metadata.tables[f"positions_{am}"]
        Base.metadata.create_all(am_engine, tables=[bronze, raw])
        click.echo(f"✓ {am}rdb ready (position_bronze + positions_{am})")
