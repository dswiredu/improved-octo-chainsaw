# dagster_etl/partitions.py
"""
Partition definitions that update automatically when you add / remove
clients in client_config.csv.

• RAW_DATES   – daily partitions for every raw-<am> asset
• CLIENTS     – StaticPartitionsDefinition built from the CSV
• CLIENT_DATE – multi-dimension (client × date) for bronze assets
"""
from __future__ import annotations

import os
from dagster import (
    DailyPartitionsDefinition,
    StaticPartitionsDefinition,
    MultiPartitionsDefinition,
)

from utils.config import get_client_config  # same helper you already use

# ── 1. RAW dates — unchanged ──────────────────────────────────────────
RAW_DATES = DailyPartitionsDefinition(start_date="2024-01-01")

# ── 2. Clients list comes from the CSV ────────────────────────────────
_ETL_LOC = os.getenv("ETL_LOC")
_CLIENT_DF = get_client_config(_ETL_LOC)  # loads client_config.csv

_unique_clients = sorted(_CLIENT_DF["client"].unique().tolist())

CLIENTS = StaticPartitionsDefinition(_unique_clients)

# ── 3. Combined dimension for bronze assets ───────────────────────────
CLIENT_DATE = MultiPartitionsDefinition({"client": CLIENTS, "date": RAW_DATES})

# Optional: export the actual list for other modules/tests
CLIENT_NAMES: list[str] = _unique_clients
