import logging
import pandas as pd
import numpy as np

from layers.recon.exceptions import (
    InputValidationException,
    ClientDataNotFoundException,
    FirmSpecificLogicException,
)
from layers.recon.datehandler import DateUtils
import layers.recon.data_processing.d1g1t_clients as dc
from layers.recon.data_processing.d1g1t import v3, v4

from layers.common.properties import Properties

logger = logging.getLogger(__name__)

POSITION_INFO = [
    "date",
    "account",
    "account_name",
    "custodian",
    "instrument",
    # "instrument_currency",
    # "cusip",
    # "ticker",
    "instrument_name",
    "instrument_type",
    # "fund_code",
]

INFO_COLS = [
    "instrument",
    "date",
    "account",
    "account_currency",
    "instrument_type",
    "fund_code",
    "instrument_currency",
    "cusip",
    "ticker",
]
METRIC_COLS = [
    "scale",
    "units",
    "units_settle",
    "price",
    "mv_clean",
    "mv_clean_ac_cad_usd",
    "mv_clean_CAD",
    "mv_clean_settle_CAD",
    "mv_clean_USD",
    "ai",
    "ai_irc",
    "mv_dirty",
    "mv_dirty_CAD",
    "mv_dirty_USD",
    "mv_dirty_ac_cad_usd",
    "bv",
    "bv_CAD",
    "bv_settle_CAD",
    "bv_USD",
    "bv_settle_USD",
    "bv_ac_cad_usd",
    "bv_instr_cad_usd",
    "acb",
]
RENAMED_METRIC_COLS = {val: f"d1g1t_{val}" for val in METRIC_COLS}

BASIS_ANLS_METRICS = [
    "bv",
    "units_settle",
    "mv_clean",
    "mv_clean_ac_cad_usd",
    "mv_clean_CAD",
    "mv_clean_settle_CAD",
    "bv_CAD",
    "bv_settle_CAD",
    "mv_clean_USD",
    "bv_settle_USD",
    "bv_USD",
    "bv_ac_cad_usd",
    "bv_instr_cad_usd",
    "total_gain",
    "total_return",
    "mv_dirty_CAD",
    "mv_dirty_USD",
    "mv_dirty_ac_cad_usd",
    "mv_dirty_t-1",
    "instrument_type",
]

BASIS_ANLS_COLS = (
    INFO_COLS + BASIS_ANLS_METRICS
)  # Update this to get more info in the basis anls

SUPPORTED_CURRENCIES = [
    "AUD",
    "BRL",
    "CAD",
    "DKK",
    "EUR",
    "GBP",
    "HKD",
    "ILS",
    "JPY",
    "MXN",
    "MYR",
    "NOK",
    "NZD",
    "CHF",
    "SGD",
    "SEK",
    "USD",
    "ZAR",
]

SETTLE_DATE_RECON_CLIENTS = [
    "burkett"
]  # For clients who need to reconclie positions for settle date


def get_client_major_version(client_version: str) -> int:
    return int(client_version.split(".")[0])


def get_basis_anls_cols(df: pd.DataFrame) -> list:
    """Since basis analytics headers are unstable we retrieve
    as many as are in BASIS_ANLS_COLS
    """
    return [x for x in df.columns if x in BASIS_ANLS_COLS]


def get_recon_custodian(df: pd.DataFrame, aliases: dict):
    res = df["custodian"].map(aliases)
    return res.fillna(df["custodian"])


def get_d1g1t_client_data(
    firm: str,
    client: str,
    path: str,
    environment: str,
    client_version: str,
    recon_funds: str,
    dt: str,
    reporting_currency: str,
    custodian_aliases: dict,
) -> pd.DataFrame:
    df_sql = get_client_sql_exract(
        client,
        path,
        environment,
    )
    df_ba = get_client_basis_analytics(
        firm,
        client,
        environment,
        client_version,
        recon_funds,
        dt,
        reporting_currency,
    )
    if not df_ba.empty:
        df_d1g1t = combine_sql_extract_and_basis_anls(df_sql, df_ba, firm)
    else:
        df_d1g1t = df_sql
    df_d1g1t.rename(columns=RENAMED_METRIC_COLS, inplace=True)
    result = get_firm_specific_logic(firm, client, df_d1g1t)
    result["custodian"] = get_recon_custodian(result, custodian_aliases)
    return result


def get_client_sql_exract(
    client: str,
    path: str,
    environment: str,
) -> pd.DataFrame:
    df_sql = read_client_sql_extract(client, path, environment)
    df_sql = process_client_sql_extract(df_sql)
    return df_sql


def read_client_sql_extract(client: str, path: str, environment: str) -> pd.DataFrame:
    s3_path = f"{path}/{environment}-{client}-latest-tracking.csv"
    logger.info(f"Retrieving d1g1t data for client: {client}...")
    try:
        df = pd.read_csv(
            s3_path, parse_dates=["date"], dtype={"instrument": str, "account": str}
        )
        return df
    except FileNotFoundError:
        msg = f"Could not find {client} sql extract at {s3_path}!"
        raise ClientDataNotFoundException(msg)


def process_client_sql_extract(df_sql: pd.DataFrame) -> pd.DataFrame:
    compute_cash_values(df_sql)
    df_sql = aggregate_holdings(df_sql)
    compute_clean_mv(df_sql)
    compute_uid(df_sql)
    return df_sql.drop(columns=["account_currency"])


def process_client_basis_analytics(df_ba: pd.DataFrame) -> pd.DataFrame:
    set_cash_price(df_ba)
    get_metric_data_by_account_currency(df_ba, "bv")
    get_metric_data_by_account_currency(df_ba, "mv_clean")
    get_metric_data_by_account_currency(df_ba, "mv_dirty")
    get_metric_data_by_instrument_currency(df_ba, "bv")
    df_ba["account"] = df_ba["account"].astype(str)
    df_ba["instrument"] = df_ba["instrument"].astype(str)
    return df_ba


def combine_sql_extract_and_basis_anls(
    df_sql: pd.DataFrame,
    df_ba: pd.DataFrame,
    firm: str,
) -> pd.DataFrame:
    anls_cols = get_basis_anls_cols(df_ba)

    merge_type = "outer" if firm in SETTLE_DATE_RECON_CLIENTS else "left"

    df_merged = df_sql.drop(columns=["mv_clean"]).merge(
        df_ba[anls_cols],
        on=["instrument", "date", "account"],
        how=merge_type,
        validate="1:1",
    )

    df_merged["total_gain"].fillna(0, inplace=True)
    df_merged["total_return"].fillna(0, inplace=True)
    get_acb(df_merged)
    return df_merged


def get_bv_for_foreign_cash_positions(df: pd.DataFrame) -> None:
    foreign_currency_cash_idx = df["instrument"].isin(SUPPORTED_CURRENCIES) & (
        ~df["instrument"].isin(["CAD", "USD"])
    )
    df.loc[foreign_currency_cash_idx, "bv_ac_cad_usd"] = df["bv"]


def get_acb(df: pd.DataFrame) -> None:
    if "bv_ac_cad_usd" in df.columns:
        df["acb"] = df["bv_ac_cad_usd"].divide(df["units"].multiply(df["scale"]))


def get_metric_data_by_account_currency(df: pd.DataFrame, metric) -> None:
    if all([x in df.columns for x in [f"{metric}_USD", f"{metric}_CAD"]]):
        df[f"{metric}_ac_cad_usd"] = np.where(
            df.account_currency == "USD", df[f"{metric}_USD"], df[f"{metric}_CAD"]
        )


def get_metric_data_by_instrument_currency(df: pd.DataFrame, metric) -> None:
    if all([x in df.columns for x in [f"{metric}_USD", f"{metric}_CAD"]]):
        df[f"{metric}_instr_cad_usd"] = np.where(
            df.instrument_currency == "USD", df[f"{metric}_USD"], df[f"{metric}_CAD"]
        )


def compute_clean_mv(df: pd.DataFrame) -> None:
    df.rename(columns={"mv": "mv_dirty"}, inplace=True)
    df["d1g1t_ai"] = df["units"] * df["scale"] * df["ai"]
    df.drop(columns=["ai"], inplace=True)
    df["mv_clean"] = df["mv_dirty"] - df["d1g1t_ai"].fillna(0)


def compute_uid(df: pd.DataFrame) -> None:
    df["UID"] = df["account"].astype(str) + "_" + df["instrument"].astype(str)


def aggregate_holdings(df: pd.DataFrame) -> pd.DataFrame:
    sum_cols = ["units", "mv"]

    position_cols = ["account", "instrument", "date"]

    first_cols = [col for col in df.columns if col not in sum_cols + position_cols]

    df = df.dropna(subset=["units"])

    agg_map = {
        **{col: "first" for col in first_cols},
        **{col: "sum" for col in sum_cols},
    }

    agg = df.groupby(position_cols).agg(agg_map).reset_index()
    return agg


def get_prices(s3_path: str) -> pd.DataFrame:
    df = pd.read_csv(s3_path, parse_dates=["date"], dtype={"instrument": str})
    return df


def get_client_static_data(s3_path: str) -> pd.DataFrame:
    static_rename_cols = {
        "account_id": "account",
        "account_custodian": "custodian",
        "instrument_id": "instrument",
    }
    df = pd.read_csv(s3_path, dtype=str)
    return df.rename(columns=static_rename_cols)


def get_data_retrieval_path(
    firm: str, client: str, environment: str, data_type: str, dte: str
) -> str:
    """Get's path to read prices, accounts and instrument data."""
    properties = Properties(environment=environment, client=client)
    s3_bucket = properties.client_s3_bucket
    default_s3_key = (
        f"s3://{s3_bucket}/{client}/exports/recon/{data_type}/{environment}"
    )
    return f"{default_s3_key}/{firm}_{dte}.csv"


def read_d1g1t_data(
    firm: str,
    client: str,
    environment: str,
    data_type: str,
    dte=DateUtils.get_last_cob_date(),
) -> pd.DataFrame:
    """
    Reads one of prices, 'static data' or basis analytics for recon purposes.
    """
    df = pd.DataFrame()
    data_retrieval_map = {
        "prices": get_prices,
    }
    if DateUtils.is_valid_date_input(dte):
        s3_path = get_data_retrieval_path(firm, client, environment, data_type, dte)
    else:
        message = f"The input {dte} is incorrect! Expected YYYY-MM-DD"
        raise InputValidationException(message)
    logger.info(f"Retrieving d1g1t {data_type} for {client} on {dte}...")
    try:
        func = data_retrieval_map.get(data_type, get_client_static_data)
        df = func(s3_path)
    except FileNotFoundError:
        msg = f"Could not find d1g1t {data_type} for client: {client} at {s3_path}!"
        logger.warning(msg)
    return df


def merge_client_data(
    anls: pd.DataFrame,
    pxs: pd.DataFrame,
    accounts: pd.DataFrame,
    instruments: pd.DataFrame,
) -> pd.DataFrame:
    """Merge static data (accounts, instruments) and prices to basis analytics"""
    anls_pxs = anls.merge(pxs, how="left", on=["date", "instrument"], validate="m:1")
    anls_pxs_accounts = anls_pxs.merge(
        accounts, how="left", on=["account"], validate="m:1"
    )
    res = anls_pxs_accounts.merge(
        instruments, how="left", on=["instrument"], validate="m:1"
    )
    return res


def get_basis_analytics(
    firm: str,
    client: str,
    environment,
    client_version: str,
    get_funds: str = "",
    dte: str = "",
    reporting_currency: str = "",
) -> pd.DataFrame:
    major_version = get_client_major_version(client_version)
    if major_version == 3:
        df = v3.get_basis_analytics(
            firm, client, environment, get_funds, dte, reporting_currency
        )
    else:
        df = v4.get_basis_analytics(
            firm, client, environment, get_funds, dte, reporting_currency
        )
    return df


def get_client_basis_analytics(
    firm: str,
    client: str,
    environment: str,
    client_version: str,
    get_funds: str = "",
    dte: str = "",
    reporting_currency: str = "",
) -> pd.DataFrame:
    try:
        anls = get_basis_analytics(
            firm,
            client,
            environment,
            client_version,
            get_funds,
            dte,
            reporting_currency,
        )
        pxs = read_d1g1t_data(firm, client, environment, "prices", dte)
        instruments = read_d1g1t_data(firm, client, environment, "instruments", dte)
        accounts = read_d1g1t_data(firm, client, environment, "accounts", dte)
        df = merge_client_data(anls, pxs, accounts, instruments)
        df = process_client_basis_analytics(df)
        return df
    except ClientDataNotFoundException:
        msg = f"Could not find basis analytics for {client}!"
        logger.warning(msg)
        return pd.DataFrame()
    except KeyError:
        msg = f"Basis analytics does not contain needed data for {client}!"
        logger.warning(msg)
        return pd.DataFrame()


def set_cash_price(df: pd.DataFrame) -> None:
    """
    Cash instruments do not have prices. Set these to 1.
    """
    cash_idx = df["instrument"].isin(SUPPORTED_CURRENCIES)
    df.loc[cash_idx, "price"] = 1


def compute_cash_values(df: pd.DataFrame) -> None:
    """
    Extract does not send mv or price for cash.
    We get mv based on logic that, for cash price is always 1 and
    mv is always the same as units
    """
    cash_idx = df.instrument.isin(SUPPORTED_CURRENCIES)
    df.loc[cash_idx, "price"] = 1
    df.loc[cash_idx, "mv"] = df["units"]


def get_firm_specific_logic(firm: str, client: str, df: pd.DataFrame):
    res = df.copy()
    try:
        cls = getattr(dc, firm.title())
        client_instance = cls(firm, client)
        res = client_instance.apply_firm_specific_d1g1t_logic(df)
        return res
    except AttributeError:
        msg = f"No firm-specific logic found for {firm} on d1g1t data."
        logger.info(msg)
        return res
    except Exception as e:
        msg = f"Could not apply {firm} specific logic to d1g1t data due to error: {e}"
        raise FirmSpecificLogicException(msg)
