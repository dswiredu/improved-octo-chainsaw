import pandas as pd
from datetime import datetime

from layers.recon.data_processing.d1g1t_clients.d1g1t_client import D1g1tClient
from layers.recon.datehandler import DateUtils, HM_DATE_FORMAT
from layers.recon.data_processing.d1g1t import read_d1g1t_data
from pytz import timezone
from layers.recon.data_processing.lookup import CCY_MAP
from layers.recon.validation import override_cash_recon_by_threshold

et = timezone("US/Eastern")


class Acp(D1g1tClient):
    def __init__(self, firm: str, client: str) -> None:
        super().__init__(firm, client)

    def get_d1g1t_account_currency(self, dte: str) -> dict:
        accounts = read_d1g1t_data(
            self.firm, self.client, "production", "accounts", dte
        )
        df = accounts[["account", "account_currency"]]
        df["account"] = df["account"]
        account_dict = df.set_index("account").to_dict()["account_currency"]
        return account_dict

    def get_fx_rates(self, dte: str) -> dict:
        recon_dte = DateUtils().get_recon_date(dte)
        ciis_dte = DateUtils.get_custodian_date(recon_dte)
        file = f"s3://d1g1t-custodian-data-ca/ciis/acp/{ciis_dte}/EOD_FXRate.dat"

        df = pd.read_csv(file, sep="|", encoding="ISO-8859-1")
        df["Currencies"] = df["FromCurrency"] + df["ToCurrency"]
        df = df.drop(["FromCurrency", "ToCurrency", "AsOfDate"], axis=1)
        for i in df.index:
            df.loc[i + 1] = [
                round(1 / df["Rate"][i], 8),
                df["Currencies"][i][-3:] + df["Currencies"][i][:-3],
            ]
        fx_dict = df.set_index("Currencies").to_dict()["Rate"]
        return fx_dict

    def update_instrument_ids(self, instruments: pd.Series) -> pd.Series:
        non_currency_idx = instruments.str.contains("_")
        instruments.loc[non_currency_idx] = instruments.str[:-4]
        return instruments

    def process_fx(self, d1g1t_df: pd.DataFrame) -> pd.DataFrame:
        d1g1t_df["Instrument CCY"] = d1g1t_df["instrument"].str[-3:]
        d1g1t_df["instrument"] = self.update_instrument_ids(d1g1t_df["instrument"])
        dte = datetime.strftime(d1g1t_df["date"][0], "%Y-%m-%d")
        accounts = self.get_d1g1t_account_currency(dte)
        d1g1t_df["FX"] = d1g1t_df["account"].map(accounts)
        d1g1t_df["FX"] = d1g1t_df["Instrument CCY"] + d1g1t_df["FX"]
        fx_rates = self.get_fx_rates(dte)
        d1g1t_df["FX"] = d1g1t_df["FX"].map(fx_rates)
        fx_idx = d1g1t_df["FX"].notna()
        d1g1t_df.loc[fx_idx, "d1g1t_mv_dirty"] = (
            d1g1t_df["d1g1t_mv_dirty"] * d1g1t_df["FX"]
        )
        d1g1t_df.loc[fx_idx, "d1g1t_price"] = d1g1t_df["d1g1t_price"] * d1g1t_df["FX"]
        d1g1t_df["FX"].fillna("", inplace=True)
        return d1g1t_df

    def find_and_aggregate_duplicate_positions(
        self, df: pd.DataFrame, data_source
    ) -> pd.DataFrame:
        if data_source == "d1g1t":
            df = df[df["is_dead"].isnull()]
        dupes = df[df.duplicated(subset=["date", "account", "instrument"], keep=False)]
        dupe_date = datetime.strftime(df["date"].iloc[0], "%Y-%m-%d")
        timestamp = datetime.now(et).strftime(HM_DATE_FORMAT)
        dupes.to_csv(
            f"s3://d1g1t-client-ca/acp/validation/acp_duplicates_{data_source}_{dupe_date}-{timestamp}.csv",
            index=False,
        )

        numeric_columns = df.select_dtypes(include=["number"]).columns

        res = df.groupby(["date", "account", "instrument"], as_index=False).agg(
            {
                **{col: "sum" for col in numeric_columns},
                **{col: "first" for col in df.columns if col not in numeric_columns},
            }
        )

        return res

    def apply_firm_specific_d1g1t_logic(self, d1g1t_df: pd.DataFrame) -> pd.DataFrame:
        d1g1t_df = self.process_fx(d1g1t_df)
        res = self.find_and_aggregate_duplicate_positions(d1g1t_df, "d1g1t")
        return res

    def apply_firm_specific_custodian_logic(
        self, custodian: str, custodian_df: pd.DataFrame
    ) -> pd.DataFrame:
        res = self.find_and_aggregate_duplicate_positions(custodian_df, "custodian")
        return res

    @staticmethod
    def override_cash_recon(df: pd.DataFrame) -> None:
        suffix = "_reconciled"
        client_cash_threshold = 100
        diffs = df.filter(like=suffix)
        metrics = [x.split(suffix)[0] for x in diffs.columns]
        cash_idx = df["instrument"].isin(CCY_MAP.values())
        for metric in metrics:
            cash_reconciled = df[f"{metric}_diff"].abs() <= client_cash_threshold
            df.loc[cash_idx, f"{metric}{suffix}"] = cash_reconciled

    def apply_recon_post_processing_logic(self, df: pd.DataFrame) -> pd.DataFrame:
        override_cash_recon_by_threshold(df, 10)
        df = df[
            [
                "date",
                "account",
                "account_name",
                "custodian",
                "instrument",
                "instrument_name",
                "Instrument CCY",
                "Settlement CCY",
                "FX",
                "d1g1t_units",
                "custodian_units",
                "units_diff",
                "units_reconciled",
                "d1g1t_price",
                "custodian_price",
                "price_diff",
                "price_reconciled",
                "d1g1t_mv_dirty",
                "custodian_mv_dirty",
                "mv_dirty_diff",
                "mv_dirty_reconciled",
                "CustomerCode",
                "Note",
                "custodian_mapper",
            ]
        ]
        return df
