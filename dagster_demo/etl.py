import os
from typing import Any
from dotenv import load_dotenv
import logging

import pandas as pd

import connectors as conn
from utils.config import get_asset_manager_config, get_client_config
from utils.logger import configure_logger
from utils.exceptions import InputValidationException, ImproperConfigurationException
from importer.extractor import Extractor


load_dotenv()
configure_logger()

LOG = logging.getLogger(__name__)


def get_datasource() -> Any:
    """
    Get a datasource class to be used throughout code (as context)
    based on DB_DRIVER_KEY in env.
    Defining this here since we might switch to other source.
    """
    src_name = os.environ["DB_DRIVER_KEY"]
    try:
        src = getattr(conn, src_name)
        return src
    except AttributeError:
        msg = "DataSource name must be defined among connectors."
        raise InputValidationException(msg)


def main(client: str, dte: str) -> None:

    LOG.info("Reading client config...")
    etl_loc = os.environ["ETL_LOC"]
    client_config = get_client_config(etl_loc)
    config = client_config.query("client == @client")

    if config.empty:
        msg = f"Client : {client} missing from client config."
        raise ImproperConfigurationException(msg)

    LOG.info("Getting data source...")
    datasource = get_datasource()

    am_configs = get_asset_manager_config(etl_loc)
    for am in set(config["asset_manager"]):
        LOG.info(f"Running extractor for {am}...")
        try:
            if am not in am_configs:
                msg = f"{am} not found in asset manager config."
                LOG.exception(msg)
                continue

            am_config = am_configs[am]
            extractor = Extractor(datasource, am, am_config)
            ex_df = extractor.run(dte)
        except Exception as err:
            LOG.exception(err)


# if __name__ == "__main__":
#     client = "aebe_isa"
#     dte = "2025-07-08"
# aebe_isa|2025-07-08
#     main(client, dte)
