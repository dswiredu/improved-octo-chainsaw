import logging
from typing import Optional

import pandas as pd
from layers.recon.data_processing.d1g1t import (
    METRIC_COLS,
    POSITION_INFO,
    SUPPORTED_CURRENCIES,
)

logger = logging.getLogger(__name__)

DEFAULT_THRESHOLD_SETTING = {"threshold_type": "absolute", "threshold": 0.01}


def compare_frames(
    custodian_frame: pd.DataFrame, d1g1t_frame: pd.DataFrame
) -> pd.DataFrame:
    merge_cols = ["date", "account", "instrument"]

    # Per Dalia Kronenberg
    merged_frame = pd.merge(
        d1g1t_frame, custodian_frame, how="outer", on=merge_cols, validate="1:1"
    )
    return merged_frame


def reconcile_metrics(
    df: pd.DataFrame, threshold_settings: dict, metrics: list
) -> None:
    for metric in metrics:
        threshold_setting = threshold_settings.get(metric, DEFAULT_THRESHOLD_SETTING)
        us, them = df[f"d1g1t_{metric}"], df[f"custodian_{metric}"]
        df[f"{metric}_diff"] = us - them
        dif = df[f"{metric}_diff"]
        df[f"{metric}_reconciled"] = apply_recon_rules(us, them, dif, threshold_setting)
    if all(x in metrics for x in ["price", "units"]):  # FEA-150
        tiny_units_idx = abs(df["custodian_units"]) < 1e-4
        missing_units_idx = df["custodian_units"].isna()
        dead_positions_idx = tiny_units_idx | missing_units_idx
        df.loc[dead_positions_idx, "price_reconciled"] = True
    if any(x.startswith("bv") for x in metrics):
        handle_missing_currency_book_values(df, metrics)


def handle_missing_currency_book_values(df: pd.DataFrame, metrics: list) -> None:
    # FEA-281 point 4: If custodian data is not available in particular currency we would
    # consider the bv_reconciled in that currency is TRUE as long as the other currency
    # is available
    if all(x in metrics for x in ["bv_CAD", "bv_USD"]):
        bv_cad_missing_idx = (
            df["custodian_bv_CAD"].isna() & df["custodian_bv_USD"].notna()
        )
        df.loc[bv_cad_missing_idx, "bv_CAD_reconciled"] = True
        bv_usd_missing_idx = (
            df["custodian_bv_USD"].isna() & df["custodian_bv_CAD"].notna()
        )
        df.loc[bv_usd_missing_idx, "bv_USD_reconciled"] = True
    if all(x in metrics for x in ["bv_settle_CAD", "bv_settle_USD"]):
        bv_cad_missing_idx = (
            df["custodian_bv_settle_CAD"].isna() & df["custodian_bv_settle_USD"].notna()
        )
        df.loc[bv_cad_missing_idx, "bv_settle_CAD_reconciled"] = True
        bv_usd_missing_idx = (
            df["custodian_bv_settle_USD"].isna() & df["custodian_bv_settle_CAD"].notna()
        )
        df.loc[bv_usd_missing_idx, "bv_settle_USD_reconciled"] = True


def apply_recon_rules(
    us: pd.Series, them: pd.Series, dif: pd.Series, threshold_setting: dict
) -> pd.Series:
    threshold = threshold_setting["threshold"]
    if threshold_setting["threshold_type"] == "relative":
        relative_dif = dif.copy()
        non_zero_mask = them != 0
        relative_dif.loc[non_zero_mask] = (
            dif[non_zero_mask] / them[non_zero_mask]
        ).abs()
        relative_dif.loc[~non_zero_mask] = 0
        res = relative_dif <= threshold
    else:
        res = dif.abs() <= threshold

    true_idx = (us.fillna(0) - them.fillna(0)).abs() <= threshold

    res.loc[true_idx] = True
    return res


def _metric_recon_cols(metric: str) -> list:
    return [
        f"d1g1t_{metric}",
        f"custodian_{metric}",
        f"{metric}_diff",
        f"{metric}_reconciled",
    ]


def get_recon_return_cols(
    df: pd.DataFrame, metrics: list, additional_cols: Optional[list]
):
    metric_return_cols = [_metric_recon_cols(metric) for metric in metrics]
    return_cols = POSITION_INFO + sum(metric_return_cols, [])
    recon_return_cols = return_cols + additional_cols + ["Note", "custodian_mapper"]
    # Identify which columns of recon_return_cols are in recon_results.columns
    recon_return_cols = [col for col in recon_return_cols if col in df.columns]
    missing_columns = set(recon_return_cols) - set(df.columns)
    if missing_columns:
        logger.warning(
            f"The following columns are not present in recon_results: {missing_columns}"
        )
    return recon_return_cols


def get_all_client_metrics(df: pd.DataFrame, metric_map: dict) -> list:
    """Get all custodian metrics and reorder them"""
    metric_lists = metric_map.values()
    metrics = set(sum(metric_lists, []))
    sort_order = {v: i for i, v in enumerate(METRIC_COLS)}
    metrics = sorted(metrics, key=lambda v: sort_order[v])
    final_metrics = []
    drop_metrics = []
    for metric in metrics:
        metric_pair = [f"d1g1t_{metric}", f"custodian_{metric}"]
        if all(col in df.columns for col in metric_pair):
            final_metrics.append(metric)
        else:
            drop_metrics.extend(metric_pair)

    if drop_metrics:
        logger.warning(
            "Error: The following metrics are not reconclied due to missing data: %s",
            ", ".join(drop_metrics),
        )
    return final_metrics


def get_custodian_missing_metrics(custodian: str, metric_map: dict) -> list:
    """
    Get list of metrics not sent by a custodian
    """
    custodian_metrics = metric_map[custodian]
    other_metrics = sum(metric_map.values(), [])
    return list(set(other_metrics) - set(custodian_metrics))


def override_ignored_account_recon(
    df: pd.DataFrame, ignored_accounts: Optional[set]
) -> None:
    metric_columns = [x for x in df.columns if x.endswith("_reconciled")]
    if ignored_accounts:
        note = "Account ignored during reconciliation"
        ignore_idx = df["account"].isin(ignored_accounts)
        for col in metric_columns:
            df.loc[ignore_idx, col] = True
            df.loc[ignore_idx, "Note"] = note


def override_cash_metric_recon_to_true(df: pd.DataFrame, metric: str) -> None:
    df.loc[df["instrument"].isin(SUPPORTED_CURRENCIES), f"{metric}_reconciled"] = True


def override_cash_recon_by_threshold(df: pd.DataFrame, client_cash_threshold) -> None:
    suffix = "_reconciled"
    diffs = df.filter(like=suffix)
    metrics = [x.split(suffix)[0] for x in diffs.columns]
    cash_idx = df["instrument"].isin(SUPPORTED_CURRENCIES)
    note_idx = df["Note"].isna() | (df["Note"] == "")
    for metric in metrics:
        cash_reconciled = (
            df[f"d1g1t_{metric}"].fillna(0) - df[f"custodian_{metric}"].fillna(0)
        ).abs() <= client_cash_threshold
        df.loc[cash_idx & note_idx, f"{metric}{suffix}"] = cash_reconciled


def reconcile_miscellaneous(
    df: pd.DataFrame, metric_map: dict, ignored_accounts: Optional[set] = None
) -> None:
    # If all custodians have the same metrics "Note" column will be blank
    df["Note"] = ""
    for custodian, metrics in metric_map.items():
        missin_metrics = get_custodian_missing_metrics(custodian, metric_map)
        if len(missin_metrics) == 0:
            continue

        note = f"{custodian} does not provide the following metrics : {', '.join(x for x in missin_metrics)}."
        custodian_idx = df["custodian_mapper"] == custodian
        df.loc[custodian_idx, "Note"] = note

        for metric in missin_metrics:
            df.loc[custodian_idx, f"{metric}_reconciled"] = True
    override_ignored_account_recon(df, ignored_accounts)
    for metric in ["acb", "price"]:
        if any(metric in metrics for metrics in metric_map.values()):
            override_cash_metric_recon_to_true(df, metric)


def get_account_custodian_map(df: pd.DataFrame) -> dict:
    account_custodians = (
        df[["account", "custodian"]].dropna().drop_duplicates(subset=["account"])
    )
    return account_custodians.set_index("account").to_dict()["custodian"]


def get_account_custodians(df: pd.DataFrame) -> pd.DataFrame:
    account_custodians = get_account_custodian_map(df)
    res = df.drop(columns=["custodian"])
    res["custodian"] = (
        res["account"].map(account_custodians).fillna(df["custodian_mapper"])
    )
    return res


def validate_custodian_data(
    custodian_frame: pd.DataFrame,
    d1g1t_frame: pd.DataFrame,
    threshold_settings: dict,
    custodian_metric_map: dict,
    ignored_accounts: Optional[set],
    additional_output_columns: Optional[list],
) -> pd.DataFrame:
    logger.info("Comparing data...")
    recon_frame = compare_frames(custodian_frame, d1g1t_frame)
    logger.info("Reconciling...")
    return_metrics = get_all_client_metrics(recon_frame, custodian_metric_map)
    reconcile_metrics(recon_frame, threshold_settings, return_metrics)
    reconcile_miscellaneous(recon_frame, custodian_metric_map, ignored_accounts)
    recon_results = get_account_custodians(recon_frame)
    recon_return_cols = get_recon_return_cols(
        recon_results, return_metrics, additional_output_columns
    )
    return recon_results[recon_return_cols]
