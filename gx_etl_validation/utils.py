import json
import pandas as pd


def load_expectations_config(path):
    with open(path, "r") as f:
        return json.load(f)

def run_custom_validations(df, module):
    """Run any `check_...` funcs in a module; return list of dicts."""
    results = []
    for name in dir(module):
        if name.startswith("check_"):
            fn = getattr(module, name)
            if callable(fn):
                results.append(fn(df))
    return results

def split_data_by_results(df, results):
    """Return (good_rows_df, bad_rows_df) given list of failure dicts."""
    bad_idx = set()
    for r in results:
        bad_idx.update(r.get("failed_indices", []))
    bad_df = df.loc[sorted(bad_idx)]
    good_df = df.drop(index=bad_idx)
    return good_df, bad_df
