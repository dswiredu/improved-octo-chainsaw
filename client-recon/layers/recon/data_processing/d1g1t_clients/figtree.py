import pandas as pd
import numpy as np
from datetime import datetime
import logging

from layers.recon.datehandler import STD_DATE_FORMAT
from layers.recon.data_processing.d1g1t_clients.d1g1t_client import D1g1tClient
from layers.recon.data_processing.d1g1t import read_d1g1t_data

logger = logging.getLogger(__name__)


class Figtree(D1g1tClient):
    def __init__(self, firm: str, client: str) -> None:
        super().__init__(firm, client)
        self.position_cols = ["date", "account", "instrument"]
        self.d1g1t_str_cols = ["instrument_name", "account_name", "custodian"]
        self.cust_str_cols = ["Position_Date"]
        self.instrument_map_file = "s3://d1g1t-client-us/figtree/reconciliation/figtree-daily-recon_cash-agg.csv"
        self.recon_metrics = ["units", "price", "mv_clean_USD"]

        # Morgan Stanley
        self.ms_account_path = "s3://d1g1t-client-us/figtree/reconciliation/figtree-morgan-stanley-accounts.csv"
        self.ms_holding_path = (
            "s3://d1g1t-production-file-transfer-us-east-1/figtree/for_figtree"
            "/recon/morgan_stanley/daily/merged_extracts"
        )
        self.ms_col_map = {
            "prior_close_as_of": "date",
            "account_id": "account",
            "product_type": "product_type",
            "name": "ms_name",
            "symbol": "symbol",
            "cusip": "ms_cusip",
            "prior_close_last_dollar": "custodian_price",
            "quantity": "custodian_units",
            "prior_close_market_value_dollar": "custodian_mv_clean_USD",
            "extract_date": "file_date",
        }
        self.ms_num_cols = [
            "quantity",
            "prior_close_market_value_dollar",
            "prior_close_last_dollar",
        ]
        self.ms_str_cols = ["account_id", "name", "cusip"]
        self.ms_cash_map = {
            "99XFCA024": "AUD",
            "061871901": "USD",
            "99XFCA032": "CAD",
            "99XFCA057": "EUR",
            "99XFCA081": "JPY",
            "99XA5J545": "NOK",
            "99XFCA065": "GBP",
        }

    @property
    def ms_accounts(self):
        df = pd.read_csv(self.ms_account_path, dtype=str)
        return set(df["Account ID"])

    def get_ms_security_join_key(self, df: pd.DataFrame) -> pd.Series:
        cash_table = pd.DataFrame(
            self.ms_cash_map.items(), columns=["cusip", "currency_id"]
        )
        df = df.merge(cash_table, on="cusip", how="left")
        df["join_key"] = (
            df["DesiredSecurityID"]
            .fillna(df["instrument"])
            .fillna(df["currency_id"])
            .fillna(df["symbol"])
            .fillna(df["name"])
        )
        return df["join_key"]

    def get_pcr_instrument_cusip_map(self, dte: str) -> dict:
        instruments = read_d1g1t_data(
            self.firm, self.client, "production", "instruments", dte
        )
        df = instruments[instruments["instrument"].str.match(r"^pcr_\d+$")]
        df = df[~(df["cusip"].isin(self.ms_cash_map.keys()))]
        df = df[df.cusip.notnull()]
        return df

    def get_ms_instruments(self, df: pd.DataFrame) -> pd.Series:
        """Get security_join_key, get the instrument-cusip map from d1g1t
        and retrieve the pcr instruments.
        """
        file_dte = df["prior_close_as_of"].iloc[0].strftime("%Y-%m-%d")
        vanilla_instruments = self.get_pcr_instrument_cusip_map(file_dte)
        sec_map_with_cusip = pd.read_csv(
            "s3://d1g1t-production-file-transfer-us-east-1/figtree/for_d1g1t/morgan_stanley/fx_positions/"
            "multi-fx-positions.csv"
        )
        df["cusip"].replace("-", np.nan)
        df = df.merge(
            sec_map_with_cusip,
            left_on=["account_id", "cusip"],
            right_on=["AccountID", "cusip"],
            how="left",
        )
        df = df.merge(vanilla_instruments, on="cusip", how="left")
        instrument = self.get_ms_security_join_key(df)
        return instrument

    @staticmethod
    def aggregate_ms_holdings(df: pd.DataFrame) -> pd.DataFrame:
        agg_map = {
            "prior_close_last_dollar": "first",
            "quantity": sum,
            "prior_close_market_value_dollar": sum,
        }
        position_cols = ["prior_close_as_of", "account_id", "instrument"]
        agg = df.groupby(position_cols).agg(agg_map).reset_index()
        return agg

    def ms_process_pure_cash(self, df: pd.DataFrame) -> pd.DataFrame:
        pure_cash_idx = (df["product_type"] == "Cash, MMF and BDP") & (
            df["name"] == "Cash"
        )
        df.loc[pure_cash_idx, "quantity"] = df["prior_close_market_value_dollar"]
        df.loc[pure_cash_idx, "cusip"] = "USD"
        return df

    def ms_get_fx_rates(self, df: pd.DataFrame) -> dict:
        df["fx_rate"] = 1 / df["prior_close_last_dollar"].astype(float)
        fx_rates = df[["cusip", "fx_rate"]].set_index("cusip")["fx_rate"].to_dict()
        return fx_rates

    def ms_process_fx_cash(self, df: pd.DataFrame) -> pd.DataFrame:
        fx_rate_idx = df["product_type"] == "Savings & Time Deposits"
        fx_rate = df[fx_rate_idx].drop_duplicates(subset=["cusip"])
        fx_rate["cusip"] = fx_rate["cusip"].map(self.ms_cash_map)
        ms_fx_rates = self.ms_get_fx_rates(fx_rate)
        fx_cash_idx = df["product_type"] == "FX Currencies"
        df.loc[fx_cash_idx, "fx_rate"] = df["symbol"].map(ms_fx_rates)
        df.loc[fx_cash_idx, "quantity"] = (
            df["fx_rate"] * df["prior_close_market_value_dollar"]
        )
        return df

    def process_ms_holdings(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in self.ms_num_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df = self.ms_process_pure_cash(df)
        df = self.ms_process_fx_cash(df)
        df["instrument"] = self.get_ms_instruments(df)
        res = self.aggregate_ms_holdings(df)
        return res.rename(columns=self.ms_col_map)

    def get_ms_holdings(self):
        dte = datetime.today().strftime(STD_DATE_FORMAT)
        ms_file = f"{self.ms_holding_path}/{dte}_daily_holdings.csv"
        df = pd.read_csv(
            ms_file,
            usecols=self.ms_col_map.keys(),
            parse_dates=["prior_close_as_of", "extract_date"],
            dtype={x: str for x in self.ms_str_cols},
        )
        fill_blank_dte = df["prior_close_as_of"].max().strftime(STD_DATE_FORMAT)
        blank_date_idx = df["prior_close_as_of"].isnull()
        df.loc[blank_date_idx, "prior_close_as_of"] = fill_blank_dte
        res = self.process_ms_holdings(df)
        return res

    @property
    def instrument_map(self):
        mapp = pd.read_csv(self.instrument_map_file, dtype=str)
        return mapp

    def get_correct_ids(self, df: pd.DataFrame) -> pd.DataFrame:
        res = df.merge(
            self.instrument_map,
            how="left",
            left_on=["instrument"],
            right_on=["wrong_id"],
            validate="m:1",
        )
        return res

    @staticmethod
    def update_cash_security(df: pd.DataFrame) -> None:
        df["instrument"] = df["correct_id"].fillna(df["instrument"])

    def aggregate_positions(self, df: pd.DataFrame, side="d1g1t") -> pd.DataFrame:
        aggregation_map = {}
        if side == "d1g1t":
            aggregation_map.update({x: "first" for x in self.d1g1t_str_cols})
        else:
            aggregation_map.update({x: "first" for x in self.cust_str_cols})
        num_cols = [  # sum numeric columns
            x for x in df.columns if ((x.startswith(f"{side}_")) & ("price" not in x))
        ]
        price_cols = [x for x in df.columns if "price" in x]
        position_date_col = ["Position_Date"] if "Position_Date" in df.columns else []
        aggregation_map.update({x: "sum" for x in num_cols})
        aggregation_map.update({x: "first" for x in price_cols + position_date_col})
        agg = df.groupby(self.position_cols).agg(aggregation_map).reset_index()
        return agg

    @staticmethod
    def drop_fx_clone_ids(df: pd.DataFrame):
        clone_idx = (df["instrument"].str.contains(r"^pcr_.*_\w{3}$", na=False)) & (
            df["custodian"] == "Stifel Nicolaus"
        )
        df.loc[clone_idx, "instrument"] = df.loc[clone_idx, "instrument"].str[:-4]

    def apply_firm_specific_d1g1t_logic(self, d1g1t_df: pd.DataFrame) -> pd.DataFrame:
        df = self.get_correct_ids(d1g1t_df)
        self.drop_fx_clone_ids(df)
        self.update_cash_security(df)
        df["instrument_name"] = df["correct_id_instrument_name"].fillna(
            df["instrument_name"]
        )
        res = self.aggregate_positions(df)
        return res

    def apply_pcr_initial_logic(self, custodian_df: pd.DataFrame) -> pd.DataFrame:
        df = self.get_correct_ids(custodian_df)
        self.update_cash_security(df)
        res = self.aggregate_positions(df, side="custodian")
        return res

    def apply_pcr_logic(self, custodian_df: pd.DataFrame) -> pd.DataFrame:
        pcr = self.apply_pcr_initial_logic(custodian_df)
        try:
            ms = self.get_ms_holdings()
            pcr_only = pcr[~(pcr.account.isin(ms["account"]))]
            res = pd.concat([pcr_only, ms])
            return res
        except Exception as err:
            msg = (
                f"Got the following error while processing Morgan Stanley data: {err}."
            )
            logger.error(msg)
        res = pcr[~(pcr.account.isin(self.ms_accounts))]
        return res

    def apply_firm_specific_custodian_logic(
        self, custodian: str, custodian_df: pd.DataFrame
    ) -> pd.DataFrame:
        if custodian == "pcr":
            res = self.apply_pcr_logic(custodian_df)
            return res
        else:
            return custodian_df

    def override_stale_position_recon(self, df: pd.DataFrame) -> None:
        stale_idx = pd.to_datetime(df["Position_Date"]) < pd.to_datetime(df["date"])
        for metric in self.recon_metrics:
            df.loc[stale_idx, f"{metric}_reconciled"] = "Stale Baseline"

    def apply_recon_post_processing_logic(self, df: pd.DataFrame) -> pd.DataFrame:
        self.override_stale_position_recon(df)
        return df
