# utils/lineage_tracker.py
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Tuple

from dagster import AssetKey

try:  # Dagster ≥ 1.12 (not on PyPI yet)
    from dagster import ColumnDependencies  # type: ignore

    _HAS_COLUMN_DEPS = True
except ImportError:  # Dagster 1.11.x and earlier
    ColumnDependencies = dict  # type: ignore
    _HAS_COLUMN_DEPS = False


class LineageTracker:
    """Light-weight column-lineage helper (works on every Dagster version)."""

    def __init__(self, asset_key: AssetKey) -> None:
        self.asset_key = asset_key
        self._map: Dict[str, set[Tuple[AssetKey, str]]] = defaultdict(set)

    # -----------------------------------------------------------------
    # Manual capture ---------------------------------------------------
    def add(self, target: str, *sources: str) -> None:
        for src in sources:
            self._map[target].add((self.asset_key, src))

    # -----------------------------------------------------------------
    # Automatic capture for simple assignments ------------------------
    def wrap(self, df):
        orig_setitem = df.__setitem__

        def patched(name, value):
            if isinstance(name, str):
                if hasattr(value, "name") and isinstance(value.name, str):
                    self._map[name].add((self.asset_key, value.name))
                else:
                    self._map[name].update((self.asset_key, c) for c in df.columns)
            return orig_setitem(name, value)

        df.__setitem__ = patched
        return df

    # -----------------------------------------------------------------
    # Serialisable dict you can attach as metadata (works now) ---------
    def to_metadata(self) -> dict:
        return {
            tgt: [f"{ak.to_string()}.{col}" for ak, col in sorted(srcs)]
            for tgt, srcs in self._map.items()
        }

    # ColumnDependencies once Dagster ≥ 1.12 --------------------------
    def to_dagster(self):
        if not _HAS_COLUMN_DEPS:
            return self.to_metadata()
        return {t: ColumnDependencies(list(srcs)) for t, srcs in self._map.items()}
