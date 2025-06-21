"""
validate_minimal.py  –  bare-bones Great Expectations 0.18.x
• No DataContext / YAML.  Just DataFrame + JSON expectations.
• Outputs JSON reports to reports/<YYYYMMDD>/<name>.json
-------------------------------------------------------------"""

from __future__ import annotations
import json, datetime
from pathlib import Path
import pandas as pd
import great_expectations as gx
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.core.expectation_configuration import (
    ExpectationConfiguration,
)
from great_expectations.dataset import PandasDataset

# ─────────── your data-fetch logic ───────────
def get_dataframe(name: str) -> pd.DataFrame:
    """Replace with real extraction logic."""
    return pd.read_csv(f"data/{name}.csv")

# ─────────── helper: JSON → ExpectationSuite ───────────
def suite_from_json(name: str, json_path: Path) -> ExpectationSuite:
    payload = json.loads(json_path.read_text())
    suite = ExpectationSuite(expectation_suite_name=f"{name}_suite")
    suite.expectations = [
        ExpectationConfiguration(**e) for e in payload.get("expectations", [])
    ]
    return suite

# ─────────── minimal validation loop ───────────
NAMES = ["26N", "BlueOwl"]                  # add names freely
RUN_DATE = datetime.datetime.now().strftime("%Y%m%d")


for name in NAMES:
    REPORT_DIR = Path("reports") / name / RUN_DATE
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    cfg_path = Path("configs") / f"{name}.json"
    if not cfg_path.exists():
        print(f"⚠️  {name}: {cfg_path} missing – skipped")
        continue

    df = get_dataframe(name)
    suite = suite_from_json(name, cfg_path)

    # Wrap DF in PandasDataset and validate
    ds = PandasDataset(df, expectation_suite=suite)
    result = ds.validate(result_format="COMPLETE")

    out_json = REPORT_DIR / f"{name}.json"
    out_json.write_text(json.dumps(result.to_json_dict(), indent=2), encoding="utf-8")

    stats = result.statistics
    print(
        f"✅  {name}: {'PASS' if result.success else 'FAIL'} "
        f"({stats['successful_expectations']}/{stats['evaluated_expectations']} ok) → {out_json}"
    )

print("\n🎉  Finished.  Open the JSON files in reports/<date>/")
