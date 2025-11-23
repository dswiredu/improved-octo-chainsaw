import os

import pandas as pd
from utils.common import load_json


def get_asset_manager_config(loc: str) -> dict[str]:
    dict_path = os.path.join(loc, "config", "asset_manager_config.json")
    return load_json(dict_path)


def get_client_config(loc: str) -> pd.DataFrame:
    """
    Gets the client config as a dataframe.
    """
    csv_path = os.path.join(loc, "config", "client_config.csv")
    df = pd.read_csv(csv_path, dtype={"allocation": float})
    return df
