# importer/asset_mangers/asset_manager.py
import logging
from abc import ABC, abstractmethod
from typing import List, Tuple

import pandas as pd
from dagster import AssetKey

from utils.lineage_tracker import LineageTracker

LOG = logging.getLogger(__name__)


class AssetManager(ABC):
    """Base class every AM<X> subclass extends."""

    def __init__(self, name: str, feed_path: str) -> None:
        self.name = name
        self.feed_path = feed_path

    # ────────── ABSTRACTS (signature CHANGE!) ─────────────────────────
    @abstractmethod
    def read_data(self, dte: str, source_files: List[str]) -> pd.DataFrame:
        """
        Load raw files for *dte* and APPEND every file path you touch to
        *source_files*.  That’s how we later expose file-level lineage.
        """

    @abstractmethod
    def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Transform the dataframe (casts, math, etc.)."""

    # ────────── NEW: one helper every raw asset will call ─────────────
    def get_df_with_lineage(
        self, dte: str, asset_key: AssetKey
    ) -> Tuple[pd.DataFrame, LineageTracker, List[str]]:
        """
        Return (final_df, lineage_tracker, [source files]) with automatic
        column-level tracking already applied.
        """
        source_files: List[str] = []

        # 1️⃣ read & wrap
        df = self.read_data(dte, source_files)
        tracker = LineageTracker(asset_key)
        df = tracker.wrap(df)  # ← monkey-patch __setitem__

        # 2️⃣ transform
        df = self.process_data(df)

        return df, tracker, source_files
