"""
Run:  python run_validation.py
Creates:
  outputs/<file>/<YYYYMMDD_HHMMSS>/{passed,failed}.csv
  reports/html/ …   (flat GX Data-Docs)
"""

import json, importlib.util
from datetime import datetime
from pathlib import Path

import pandas as pd
from great_expectations.data_context import get_context
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.core.expectation_configuration import ExpectationConfiguration
from great_expectations.core.batch import RuntimeBatchRequest

from utils import load_expectations_config, run_custom_validations, split_data_by_results

# ------------------------------------------------------------------
DATA_FILES = [
    dict(name="Base_case.csv",
         expectations="configs/base_case_expectations.json",
         custom="custom_checks/base_case.py"),
    dict(name="curves.csv",
         expectations="configs/curves_expectations.json",
         custom=None),
]

RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
CTX = get_context()                       # picks up gx/great_expectations.yml
DATASOURCE = "my_runtime_ds"              # created on the fly
OUT_ROOT = Path("outputs")
HTML_ROOT = Path("reports/html")

# ------------------------------------------------------------------
# 1. register a *fluent* runtime datasource once (if not present)
if DATASOURCE not in CTX.datasources:
    CTX.sources.add_pandas(name=DATASOURCE)         # no base_directory needed

# ------------------------------------------------------------------
for cfg in DATA_FILES:
    file_name   = cfg["name"]
    asset_name  = file_name                          # use filename as asset
    csv_path    = Path("data") / file_name
    suite_name  = asset_name.replace(".csv", "_suite")

    # 2. create / update expectation suite from JSON
    exp_json = load_expectations_config(cfg["expectations"])
    try:
        suite = CTX.get_expectation_suite(suite_name)
    except Exception:
        suite = ExpectationSuite(expectation_suite_name=suite_name)
    suite.expectations = [ExpectationConfiguration(**e) for e in exp_json["expectations"]]
    
    CTX.add_or_update_expectation_suite(expectation_suite=suite)

    # 3. build RuntimeBatchRequest
    batch_request = RuntimeBatchRequest(
        datasource_name=DATASOURCE,
        data_connector_name="default_runtime_data_connector_name",
        data_asset_name=asset_name,
        runtime_parameters={"path": str(csv_path)},
        batch_identifiers={"default_identifier_name": "default_id"},
    )

    # 4. validate
    validator = CTX.get_validator(batch_request=batch_request,
                                  expectation_suite_name=suite_name)
    chk_result = validator.validate()

    # 5. build flat HTML docs
    try:
        CTX.build_data_docs()
    except Exception as e:
        print(f"⚠️  Data-docs build skipped: {e}")

    # 6. custom checks
    df = pd.read_csv(csv_path)
    custom_res = []
    if cfg["custom"]:
        spec = importlib.util.spec_from_file_location("custom_module", cfg["custom"])
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        custom_res = run_custom_validations(df, mod)

    good_df, bad_df = split_data_by_results(df, custom_res)

    # 7. save outputs
    run_dir = OUT_ROOT / asset_name.replace(".csv", "") / RUN_ID
    run_dir.mkdir(parents=True, exist_ok=True)
    good_df.to_csv(run_dir / "passed.csv", index=False)
    bad_df .to_csv(run_dir / "failed.csv", index=False)
    with open(run_dir / "validation_result.json", "w") as f:
        json.dump(chk_result.to_json_dict(), f, indent=2)

    print(f"✅ {file_name} done → {run_dir}")

print("\n🎉  All validations complete.  Open reports/html/index.html to view Data-Docs.")
