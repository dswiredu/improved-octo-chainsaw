import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from database.base import Base
from database.models import common, asset_manager

from dotenv import load_dotenv

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def _include_object(obj, name, type_, reflected, compare_to):
    """
    Decide whether Alembic should consider *name* for the DB we’re
    currently migrating.

    Naming conventions you established:
      • client lookup DB  → <client>rdb      (e.g. aebe_isardb, guardianrdb)
      • asset-manager DB → <am>rdb          (e.g. 26nrdb, himcordb)

    Rules:
      ─ client  DBs keep only lookup tables (not position_bronze, positions_*)
      ─ manager DBs keep position_bronze and their own positions_<am> table
    """
    if type_ != "table":
        return True                         # don’t filter indexes/columns

    db_name = context.get_x_argument(as_dictionary=True).get("db_name", "")
    if not db_name.endswith("rdb"):         # safety—shouldn’t happen
        return True

    am_code = db_name[:-3]                  # strip the trailing 'rdb'

    # ─── asset-manager DB ─────────────────────────────────────────────
    if name == "position_bronze":
        return db_name != f"{am_code}isardb"    # True for AM DBs, False for client DB
    if name.startswith("positions_"):
        return name == f"positions_{am_code}"   # keep only its own raw table

    # ─── client lookup DB  ────────────────────────────────────────────
    # Everything else (country, instrument, …) belongs only in client DBs
    return name not in {"position_bronze"} and not name.startswith("positions_")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def _build_url_from_env() -> str:
    from connectors.mysql_connector import MySQLDataSource
    ds = MySQLDataSource(
        dbname=os.getenv("ALEMBIC_DBNAME", "aebe_isardb"),
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        port=int(os.getenv("DB_PORT", 3306)),
    )
    return ds.dsn


def run_migrations_online() -> None:
    db_url = (
        context.get_x_argument(as_dictionary=True).get("db_url")
        or _build_url_from_env()
    )

    connectable = engine_from_config(
        {"sqlalchemy.url": db_url},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_object=_include_object,   # ← filter added
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
