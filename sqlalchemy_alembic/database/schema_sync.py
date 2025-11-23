# database/schema_sync.py
"""
Programmatic “makemigrations + migrate” helper.
• Autogenerates a temp Alembic revision in RAM.
• Immediately runs upgrade head against the same connection.
• Discards the temp file.

You can call sync_db(url, db_name) for any number of databases.
"""
from tempfile import TemporaryDirectory
from pathlib import Path
from typing import Tuple

from alembic import command, config
from alembic.script import ScriptDirectory
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from database.base import Base
from database.models import common, asset_manager  # registers tables

# -- small helper to build DSN strings just like _engine() ------------------
from connectors.mysql_connector import MySQLDataSource

from dotenv import load_dotenv
from os import getenv

load_dotenv

def get_datasource(db_name: str) -> str:

    ds = MySQLDataSource(
        dbname=db_name,
        host=getenv("DB_HOST", "localhost"),
        user=getenv("DB_USER", "root"),
        password=getenv("DB_PASSWORD", ""),
        port=int(getenv("DB_PORT", 3306)),
    )
    return ds


def sync_db(db_name: str) -> None:
    """Autogenerate & apply migrations for a single physical DB."""
    ds = get_datasource(db_name)

    with ds._engine.begin() as conn, TemporaryDirectory() as tmpdir:
        # 1️⃣   bootstrap a throw-away Alembic environment ---------------
        cfg = config.Config()
        cfg.set_main_option("script_location", tmpdir)
        cfg.attributes["connection"] = conn  # reuse open connection
        ScriptDirectory(cfg)  # creates tmpdir/versions

        # 2️⃣   autogenerate          ------------------------------------
        rev_path = command.revision(
            cfg,
            message="auto-sync",
            autogenerate=True,
            head="head",
            refresh=True,  # reload ScriptDirectory after write
        )

        # 3️⃣   see if anything changed ---------------------------------
        script_dir = ScriptDirectory.from_config(cfg)
        head = script_dir.get_revision("head")
        if head and not head.module.upgrade_ops.is_empty():
            command.upgrade(cfg, "head")  # apply
            print(f"✓ schema synced for {db_name}")
        else:
            print(f"✓ no changes for {db_name}")
