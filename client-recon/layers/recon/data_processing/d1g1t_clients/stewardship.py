import pandas as pd
import logging
from layers.recon.data_processing.d1g1t_clients.d1g1t_client import D1g1tClient

logger = logging.getLogger(__name__)

currency_map = {"USD": "Canadian Dollar", "CAD": "US Dollar"}


class Stewardship(D1g1tClient):
    def __init__(self, firm: str, client: str) -> None:
        super().__init__(firm, client)

    def aggregate_cash_in_account_currency(
        self, d1g1t_df: pd.DataFrame
    ) -> pd.DataFrame:
        d1g1t_df_temp = d1g1t_df[
            ["account", "instrument", "d1g1t_units", "instrument_name"]
        ].copy()
        for currency, other_currency_name in currency_map.items():
            d1g1t_df_temp.loc[
                d1g1t_df_temp["instrument_name"] == other_currency_name, "instrument"
            ] = currency
        d1g1t_df_temp = d1g1t_df_temp.rename(
            columns={"d1g1t_units": "d1g1t_units_temp"}
        )
        d1g1t_df = pd.merge(
            d1g1t_df,
            d1g1t_df_temp,
            how="outer",
            on=["account", "instrument"],
            validate="1:1",
        )
        d1g1t_df["d1g1t_units_temp"].fillna(0, inplace=True)
        is_x_account_cash = (d1g1t_df["account_last_digit"] == "X") & (
            (d1g1t_df["instrument"] == "CAD") | (d1g1t_df["instrument"] == "USD")
        )
        d1g1t_df.loc[
            is_x_account_cash,
            "d1g1t_units",
        ] = (
            d1g1t_df["d1g1t_units"] + d1g1t_df["d1g1t_units_temp"]
        )
        for field in ["d1g1t_mv_clean_ac_cad_usd", "d1g1t_bv_ac_cad_usd"]:
            d1g1t_df.loc[
                is_x_account_cash,
                field,
            ] = d1g1t_df["d1g1t_units"]
        d1g1t_df = d1g1t_df.drop(
            d1g1t_df[
                (d1g1t_df.account_currency != d1g1t_df.instrument) & is_x_account_cash
            ].index
        )
        d1g1t_df = d1g1t_df.drop(d1g1t_df[(d1g1t_df.date == "")].index)
        return d1g1t_df

    def assign_mv_clean_currency(self, d1g1t_df: pd.DataFrame) -> pd.DataFrame:
        for currency in ["CAD", "USD"]:
            d1g1t_df.loc[
                d1g1t_df.d1g1t_account_currency == currency, "d1g1t_mv_clean"
            ] = d1g1t_df[f"d1g1t_mv_clean_{currency}"]
        idx_usd = d1g1t_df.d1g1t_account_currency == "USD"
        idx_usd_last_digit_x = (d1g1t_df.account_currency != "CAD") & (
            d1g1t_df.account_last_digit == "X"
        )
        d1g1t_df.loc[idx_usd, "d1g1t_mv_clean_ac_cad_usd"] = d1g1t_df[
            "d1g1t_mv_clean_USD"
        ]
        d1g1t_df.loc[idx_usd_last_digit_x, "d1g1t_mv_clean_ac_cad_usd"] = d1g1t_df[
            "d1g1t_mv_clean_USD"
        ]
        d1g1t_df = self.aggregate_cash_in_account_currency(d1g1t_df)
        return d1g1t_df

    def assign_custodian_account_currency(self, d1g1t_df: pd.DataFrame) -> pd.DataFrame:
        s3_file = "s3://d1g1t-nbin-custodian-data-ca-central-1/mapping-rules/NBINAccountCurrencyMapping.csv"
        try:
            df_map = pd.read_csv(s3_file, dtype=str)
            df_map.set_index("Last digit", inplace=True)
            map_d = df_map.to_dict()["Account Currency"]
            d1g1t_df["account_last_digit"] = d1g1t_df["account"].str[-1]
            d1g1t_df["d1g1t_account_currency"] = d1g1t_df["account_last_digit"].map(
                map_d
            )
            is_USD = d1g1t_df.d1g1t_account_currency == "USD"
            is_CAD = d1g1t_df.d1g1t_account_currency == "CAD"
            d1g1t_df.loc[is_USD, "d1g1t_bv_ac_cad_usd"] = d1g1t_df["d1g1t_bv_USD"]
            d1g1t_df.loc[is_CAD, "d1g1t_bv_ac_cad_usd"] = d1g1t_df["d1g1t_bv_CAD"]
        except AttributeError:
            msg = f"No data found for bloomridge at {s3_file} for apply_client_specific_d1g1t_logic!"
            logger.info(msg)
        return d1g1t_df

    def apply_firm_specific_d1g1t_logic(self, d1g1t_df: pd.DataFrame) -> pd.DataFrame:
        d1g1t_df = self.assign_custodian_account_currency(d1g1t_df)
        d1g1t_df = self.assign_mv_clean_currency(d1g1t_df)
        return d1g1t_df

    def apply_firm_specific_custodian_logic(
        self, custodian: str, custodian_df: pd.DataFrame
    ) -> pd.DataFrame:
        res = custodian_df.copy()
        return res

    def apply_recon_post_processing_logic(self, df: pd.DataFrame) -> pd.DataFrame:
        return df
