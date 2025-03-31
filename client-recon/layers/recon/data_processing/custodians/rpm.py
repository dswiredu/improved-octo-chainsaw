import pandas as pd
import logging

from layers.recon.data_processing.custodians.custodian import Custodian
from layers.recon.datehandler import DateUtils as dtU

logger = logging.getLogger(__name__)


class RPM(Custodian):
    def __init__(
        self,
        firm: str,
        client: str,
        custodian: str,
        feed: str,
        region: str,
        metrics: list,
    ) -> None:
        super().__init__(firm, client, custodian, feed, region, metrics)
        self.cash_instruments = {
            "1000001": "CAD",
            "1000005": "CAD",
            "1018194": "USD",
            "1018204": "USD",
        }

    def read_data(self, dte):
        recon_dte = dtU().get_recon_date(dte)
        rpm_dte = dtU.get_custodian_date(recon_dte)
        data_pos = self.read_data_pos(rpm_dte)

        return data_pos

    def read_data_pos(self, file_date: str):
        s3_file_pos = f"{self.feed_path}/{file_date}/DT_Holding_B1.txt"
        rpm_initial_raw = pd.read_csv(
            s3_file_pos,
            sep="|",
            dtype={
                "portfolio": str,
                "instrument": str,
                "Hold_Id": str,
                "quantity": float,
                "price": float,
                "market_value_cad": float,
                "book_value_cad": float,
                "pos_exch_rate": float,
            },
            encoding="ISO-8859-1",
        )
        formatted_date = f"{file_date[:4]}-{file_date[4:6]}-{file_date[6:]}"
        rpm_initial_raw["date"] = pd.to_datetime(formatted_date)

        return rpm_initial_raw

    def process_data(self, rpm_initial_raw):
        rpm_initial_raw["instrument"] = rpm_initial_raw["instrument"].apply(
            lambda x: x[:7] if len(x) == 14 else x
        )
        rpm_initial_raw = rpm_initial_raw.drop_duplicates(
            subset=["portfolio", "instrument"], keep="last"
        )
        rpm_initial_raw["quantity"] = (
            rpm_initial_raw["quantity"] + rpm_initial_raw["PendingUnits"]
        )
        rpm_initial_raw = rpm_initial_raw[rpm_initial_raw["quantity"] != 0]
        rpm_initial_raw.loc[rpm_initial_raw["Inv_Type"] == "G", "price"] = 1.0
        rpm_initial_raw["instrument_orig"] = rpm_initial_raw["instrument"]
        rpm_initial_raw["instrument"] = rpm_initial_raw["instrument"].replace(
            self.cash_instruments
        )
        rpm_initial_raw.loc[
            rpm_initial_raw.instrument.isin(["CAD", "USD"]), "price"
        ] = 1
        rpm_initial_raw["price"].fillna(0, inplace=True)
        rpm_initial_raw.loc[
            (rpm_initial_raw["instr_currency"] == "CAD")
            & (rpm_initial_raw["PendingUnits"] != 0),
            "market_value_cad",
        ] = (
            rpm_initial_raw["quantity"] * rpm_initial_raw["price"]
        )
        rpm_initial_raw.loc[
            (rpm_initial_raw["instr_currency"] == "USD")
            & (rpm_initial_raw["PendingUnits"] != 0),
            "market_value_cad",
        ] = (
            rpm_initial_raw["quantity"]
            * rpm_initial_raw["price"]
            * rpm_initial_raw["pos_exch_rate"]
        )
        rpm_initial_raw.loc[
            rpm_initial_raw["instr_currency"] == "USD", "market_value_cad"
        ] /= rpm_initial_raw["pos_exch_rate"]
        rpm_initial_raw.loc[rpm_initial_raw["Inv_Type"] == "G", "quantity"] = (
            rpm_initial_raw["market_value_cad"]
        )
        rpm_initial_raw = rpm_initial_raw[
            (rpm_initial_raw["market_value_cad"] != 0)
            | (rpm_initial_raw["quantity"] != 0)
        ]
        rpm_initial_raw[["quantity", "price", "market_value_cad"]] = rpm_initial_raw[
            ["quantity", "price", "market_value_cad"]
        ].fillna(0)
        rpm_initial_raw.rename(
            columns={
                "portfolio": "account",
                "quantity": "custodian_units",
                "price": "custodian_price",
                "market_value_cad": "custodian_mv_dirty",
            },
            inplace=True,
        )
        rpm_initial_raw["instr_name"] = rpm_initial_raw.groupby("instrument")[
            "instr_name"
        ].ffill()
        return rpm_initial_raw

    def get_custdn_data(self, dte) -> pd.DataFrame:
        df = self.read_data(dte)
        res = self.process_data(df)
        return res
