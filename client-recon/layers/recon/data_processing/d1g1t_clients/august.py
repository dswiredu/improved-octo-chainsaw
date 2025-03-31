import pandas as pd

from layers.recon.data_processing.d1g1t_clients.d1g1t_client import D1g1tClient


class August(D1g1tClient):
    def __init__(self, firm: str, client: str) -> None:
        super().__init__(firm, client)
        self.instrument_map_file = "s3://d1g1t-client-ca-central-1/august/recon_input/august-daily-recon_cash-agg.csv"
        self.currencies = ["AUD", "USD", "CAD", "EUR", "JPY", "NOK", "GBP"]
        self.position_cols = ["date", "account", "instrument"]
        self.d1g1t_str_cols = [
            "instrument_name",
            "account_name",
            "custodian",
            "instrument_type",
        ]

    def apply_firm_specific_d1g1t_logic(self, d1g1t_df: pd.DataFrame) -> pd.DataFrame:
        df = self.get_correct_ids(d1g1t_df)
        df = self.update_cash_security(df)
        res = self.aggregate_positions(df)
        return res

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
    def update_cash_security(df: pd.DataFrame) -> pd.DataFrame:
        df["instrument"] = df["correct_id"].fillna(df["instrument"])
        df.drop(
            ["wrong_id", "correct_id", "correct_id_instrument_name"],
            axis=1,
            inplace=True,
        )
        return df

    def aggregate_positions(self, df: pd.DataFrame, side="d1g1t") -> pd.DataFrame:
        aggregation_map = {}
        if side == "d1g1t":
            aggregation_map.update({x: "first" for x in self.d1g1t_str_cols})
        num_cols = [
            x for x in df.columns if x.startswith(f"{side}_") or x == "mv_dirty_t-1"
        ]
        aggregation_map.update({x: "sum" for x in num_cols})
        first_cols = [x for x in df.columns if x not in self.position_cols + num_cols]
        aggregation_map.update({x: "first" for x in first_cols})
        agg = df.groupby(self.position_cols, as_index=False).agg(aggregation_map)
        agg.loc[agg["instrument"].isin(self.currencies), f"{side}_price"] = 1
        return agg

    @property
    def instrument_map(self):
        mapp = pd.read_csv(self.instrument_map_file, dtype=str)
        return mapp

    def apply_firm_specific_custodian_logic(
        self, custodian: str, custodian_df: pd.DataFrame
    ) -> pd.DataFrame:
        if custodian == "pcr":
            df = self.get_correct_ids(custodian_df)
            df = self.update_cash_security(df)
            res = self.aggregate_positions(df, side="custodian")
            return res
        else:
            return custodian_df

    def apply_recon_post_processing_logic(self, df: pd.DataFrame) -> pd.DataFrame:
        return df
