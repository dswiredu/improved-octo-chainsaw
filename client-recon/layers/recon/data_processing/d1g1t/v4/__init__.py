import logging
import pathlib
import os
from datetime import datetime, timedelta

import pandas as pd
import numpy as np

from layers.recon.exceptions import (
    ClientDataNotFoundException,
    InputValidationException,
)
from layers.common.properties import Properties
from layers.recon.utils import get_json

logger = logging.getLogger(__name__)


def get_basis_analytics_path(firm: str, client: str, environment: str, dte: str) -> str:
    """Gets path to read basis analytics data."""
    properties = Properties(environment=environment, client=client)
    s3_bucket = properties.client_s3_bucket
    default_s3_key = (
        f"s3://{s3_bucket}/{client}/exports/recon/basis_analytics/{environment}"
    )
    return f"{default_s3_key}/portfolio_type/currency/{firm}_{dte}/{firm}_{dte}.csv"


def replace_cash_main_rows(df: pd.DataFrame) -> None:
    """cash rows have a '|_main' suffix (e.g. USD|_main), so we remove that"""
    main_idx = df.instrument.str.endswith("|_main")
    df.loc[main_idx, "instrument"] = df.instrument.str[:3]


def get_non_compl_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Rows that end with '|_compl' are erroneous. Drop em"""
    compl_idx = df.instrument.str.endswith("|_compl")
    return df[~compl_idx]


def get_basis_analytics_fields():
    dir_path = pathlib.Path(__file__).parent.resolve()
    filename = "basis_analytics_fields.json"
    filepath = os.path.join(dir_path, filename)
    return get_json(path=filepath)


def process_basis_analytics(df: pd.DataFrame, currency: str) -> pd.DataFrame:
    compute_returns(df)
    replace_cash_main_rows(df)
    res = get_non_compl_rows(df)
    if any(x.startswith("ai") for x in df.columns):
        compute_clean_values(res, currency)
    return res


def compute_currency_clean_values(df: pd.DataFrame, reporting_currency: str):
    """
    mv_clean is not natively available in v4 basis analytics so we:
    1. Check if mv_dirty_{currency} and ai_{currency} exist then
    2. compute mv_clean_{currency} from those columns.
    3. Do this also for settle date metrics.
    """
    other_currency = get_other_reporting_currency(reporting_currency)
    for currency in [reporting_currency, other_currency]:
        dirty_curr, ai_curr = f"mv_dirty_{currency}", f"ai_{currency}"
        if all(x in df.columns for x in [dirty_curr, ai_curr]):
            df[f"mv_clean_{currency}"] = df[dirty_curr] - df[ai_curr]

        dirty_settle_curr, ai_settle_curr = (
            f"mv_dirty_settle_{currency}",
            f"ai_settle_{currency}",
        )
        if all(x in df.columns for x in [dirty_settle_curr, ai_settle_curr]):
            df[f"mv_clean_settle_{currency}"] = (
                df[dirty_settle_curr] - df[ai_settle_curr]
            )


def compute_clean_values(df: pd.DataFrame, currency) -> None:
    df["mv_clean"] = df["mv_dirty"] - df["ai"]
    compute_currency_clean_values(df, currency)


def get_pnl(df: pd.DataFrame, prev_date_anls: pd.DataFrame) -> pd.DataFrame:
    """
    1. df has cumulative pnl for T (cumulpnl_t)
    2. prev_pnl has cumulative pnl for T-1 (cumulpnl_t1)
    2. pnl = cumulpnl_t - cumulpnl_t1
    """
    res = df.merge(
        prev_date_anls, on=["account", "instrument"], how="left", validate="1:1"
    )

    # for positions that did not exist previously on T-1
    cumulpnl_t1 = res["cumulpnl_t1"].fillna(0)
    res["total_gain"] = res["cumulpnl_t"] - cumulpnl_t1
    return res


def compute_returns(df: pd.DataFrame) -> None:
    """(cumulpnl_t - cumulpnl_t1)/(return_deniminator - cashflow)"""
    denom = (df["return_denominator"] - df["cashflow"]).abs()
    df["total_return"] = df["total_gain"].divide(denom)
    df["total_return"].replace([np.inf, -np.inf], 0, inplace=True)
    df["total_return"].fillna(0, inplace=True)


def aggregate_basis_analytics(df: pd.DataFrame) -> pd.DataFrame:
    position_cols = ["account", "instrument", "date"]
    sum_cols = np.setdiff1d(df.columns.to_list(), position_cols)
    agg_map = {**{col: "sum" for col in sum_cols}}

    agg = df.groupby(position_cols).agg(agg_map).reset_index()
    return agg


def get_previous_date_analytics(
    df: pd.DataFrame, reporting_currency: str
) -> pd.DataFrame:
    pnl_fields = ["account", "instrument", "cumulpnl_t1", "mv_dirty_t-1"]
    df["cumulpnl_t1"] = df["cumulpnl_t"].fillna(0)
    df.rename(columns={f"mv_dirty_{reporting_currency}": "mv_dirty_t-1"}, inplace=True)
    return df[pnl_fields]


def read_basis_analytics_from_path(
    s3_path: str, get_funds: str, currency: str, is_reporting_currency: bool = True
):
    if not currency:
        msg = "Firm reporting currency missing for client!"
        raise InputValidationException(msg)

    str_cols = ["Position", "CustodianAccount"]
    portfolio_types = ["client-portfolios"]
    if get_funds:
        portfolio_types.extend(["funds"])
    dfs = []

    for portfolio_type in portfolio_types:
        portfolio_file = s3_path.replace("portfolio_type", portfolio_type)
        currency_file = portfolio_file.replace("currency", currency)
        try:
            df = pd.read_csv(
                currency_file, parse_dates=["Date"], dtype={x: str for x in str_cols}
            )
            dfs.append(df)
        except FileNotFoundError:
            continue
    if dfs:
        df = pd.concat(dfs, ignore_index=True)
        analytics_fields = get_basis_analytics_fields()
        df.rename(columns=analytics_fields["column_map"], inplace=True)
        if not is_reporting_currency:
            non_reporting_flds = [
                x
                for x in analytics_fields["non-reporting-currency-fields"]
                if x in df.columns
            ]
            df = df[non_reporting_flds]
        df = get_basis_analytics_with_currency_columns(df, currency)
        res = aggregate_basis_analytics(df)
        return res
    else:
        raise ClientDataNotFoundException


def get_basis_analytics_with_currency_columns(
    df: pd.DataFrame, currency: str
) -> pd.DataFrame:
    """
    df has '_irc' (in-reporting-currency) columns.
    These are renamed to the actual 'reporting currency' columns for proper identification.
    """
    df.columns = [sub.replace("irc", currency) for sub in df.columns]
    return df


def get_recon_dates(recon_date: str) -> tuple:
    recon_date_dte = datetime.strptime(recon_date, "%Y-%m-%d")
    prev_day_dte = recon_date_dte - timedelta(days=1)
    prev_day = prev_day_dte.strftime("%Y-%m-%d")
    return recon_date, prev_day


def get_other_reporting_currency(reporting_currency: str) -> str:
    """
    Gets 'other' currency for which basis anl data should be pulled
    """
    currency_map = {"CAD": "USD", "USD": "CAD"}
    return currency_map.get(reporting_currency, reporting_currency)


def get_basis_analytics_for_currencies(
    s3_path: str, get_funds: str, reporting_currency: str
):
    reporting_currency_anls = read_basis_analytics_from_path(
        s3_path, get_funds, reporting_currency
    )
    other_currency = get_other_reporting_currency(reporting_currency)
    if other_currency != reporting_currency:
        try:
            other_currency_anls = read_basis_analytics_from_path(
                s3_path, get_funds, other_currency, is_reporting_currency=False
            )
            res = reporting_currency_anls.merge(
                other_currency_anls,
                on=["account", "instrument", "date"],
                how="left",
                validate="1:1",
            )
            return res
        except KeyError as err:
            msg = f"Could not retrieve other reporting currency: {other_currency} due to the following error :{err}"
            logger.warning(msg)
        except ClientDataNotFoundException:
            msg = (
                f"Other currency : {other_currency} is not a valid reporting currency!"
            )
            logger.warning(msg)
    else:
        msg = f"Reporting currency: {reporting_currency} is neither CAD nor USD!"
        logger.warning(msg)
        return reporting_currency_anls
    return reporting_currency_anls


def get_basis_analytics(
    firm: str,
    client: str,
    environment: str,
    get_funds: str,
    dte,
    reporting_currency: str,
) -> pd.DataFrame:
    """
    1. Gets basis analytics for recon dte including cumulative pnl for both reporting and 'other' currencies
    2. Gets cumulative pnl for previous date for both reporting and 'other' currencies and attaches to frame in 1
    3. Processes basis analytics data for that date.
    """
    recon_date, previous_date = get_recon_dates(dte)
    recon_date_path = get_basis_analytics_path(firm, client, environment, recon_date)
    prev_date_path = get_basis_analytics_path(firm, client, environment, previous_date)
    recon_date_analytics = get_basis_analytics_for_currencies(
        recon_date_path, get_funds, reporting_currency
    )
    previous_date_analytics = get_basis_analytics_for_currencies(
        prev_date_path, get_funds, reporting_currency
    )
    previous_date_analytics = get_previous_date_analytics(
        previous_date_analytics, reporting_currency
    )
    df = get_pnl(recon_date_analytics, previous_date_analytics)
    res = process_basis_analytics(df, reporting_currency)
    return res
