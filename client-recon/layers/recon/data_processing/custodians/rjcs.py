import pandas as pd
import logging

from layers.recon.data_processing.custodians.custodian import Custodian
from layers.recon.datehandler import DateUtils as dtU
from layers.recon.data_processing.d1g1t import SUPPORTED_CURRENCIES

logger = logging.getLogger(__name__)


class RJCS(Custodian):
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

        self.sr_cols = {
            "cusip": (3, 12),
            "acc_id": (12, 20),
            "current_qty": (66, 82),
            "sfk_qty": (82, 98),
            "pending_qty": (98, 114),
            "offbook_qty": (271, 287),
            "custodian_mv_clean_ac_cad_usd": (146, 162),
            "custodian_bv_ac_cad_usd": (187, 204),
        }

        self.dc_cols = {
            "acc_id": (3, 11),
            "acc_currency": (21, 22),
            "cash_balance": (95, 109),
        }

        self.sm2_cols = {
            "raw_instrument": (110, 119),
            "custodian_price": (132, 143),  # last trade price
        }

        self.process_return_columns = [
            "date",
            "account",
            "instrument",
            "custodian_units",
        ]

        self.cash_currency = {"C": "CAD", "U": "USD", "E": "EUR"}

    def transform_number_sec(self, df: pd.DataFrame, qty_type) -> float:
        """
        special logic for RJCS to transform cash/security and identify if it is a positive nuumber
        input: number that need to be transferred and type of the number - either cash or sec
        output: transferred number
        """
        res = df[qty_type].copy()
        idx = res.str[-1] == "-"
        res[idx] = "-" + res[idx].str[:-1]
        res = pd.to_numeric(res, errors="coerce")
        if qty_type == "custodian_mv_clean_ac_cad_usd":
            res = res / 100
        elif qty_type == "custodian_bv_ac_cad_usd":
            res = res / 100000
        else:
            res = res / 10000
        return res

    def transform_number_cash(self, df: pd.DataFrame) -> float:
        res = df["cash_balance"].copy()
        idx = res.str[-1] == "-"
        res[idx] = "-" + res[idx].str[:-1]
        res = pd.to_numeric(res, errors="coerce")
        res = res / 100 * (-1)
        return res

    def read_data_sr(self, file_date: str):
        """
        read data from one of the input file - sr file
        output: dataframe from sr
        """
        s3_file_sr = f"{self.feed_path}/{file_date}/sr"
        data_sr = pd.read_fwf(
            s3_file_sr,
            colspecs=list(self.sr_cols.values()),
            names=self.sr_cols.keys(),
            dtype=str,
            encoding="unicode_escape",
        )

        data_sr["current_qty"] = self.transform_number_sec(data_sr, "current_qty")
        data_sr["pending_qty"] = self.transform_number_sec(data_sr, "pending_qty")
        data_sr["sfk_qty"] = self.transform_number_sec(data_sr, "sfk_qty")
        data_sr["offbook_qty"] = self.transform_number_sec(data_sr, "offbook_qty")
        data_sr["custodian_mv_clean_ac_cad_usd"] = self.transform_number_sec(
            data_sr, "custodian_mv_clean_ac_cad_usd"
        )
        data_sr["custodian_bv_ac_cad_usd"] = self.transform_number_sec(
            data_sr, "custodian_bv_ac_cad_usd"
        )
        data_sr["qty"] = (
            data_sr["pending_qty"].fillna(0)
            + data_sr["current_qty"].fillna(0)
            + data_sr["sfk_qty"].fillna(0)
            + data_sr["offbook_qty"].fillna(0)
        )
        data_sr.rename(columns={"cusip": "raw_instrument"}, inplace=True)
        return data_sr

    def read_data_dc(self, file_date: str):
        """
        read data from one of the input file - dc file (cash balances)
        output: dataframe from dc
        """
        s3_file_dc = f"{self.feed_path}/{file_date}/dc"

        data_dc = pd.read_fwf(
            s3_file_dc,
            colspecs=list(self.dc_cols.values()),
            names=self.dc_cols.keys(),
            dtype=str,
            encoding="unicode_escape",
        )

        data_dc["qty"] = self.transform_number_cash(data_dc)

        data_dc.rename(
            columns={"acc_currency": "raw_instrument"},
            inplace=True,
        )
        return data_dc

    def read_data_sm2(self, file_date: str):
        """
        read data from one of the input file - sm2 file (scale positions)
        output: dataframe from sm2
        """
        read_data_sm2 = f"s3://d1g1t-custodian-data-ca/rjcs/secmaster/{file_date}/sm2"

        data_sm2 = pd.read_fwf(
            read_data_sm2,
            colspecs=list(self.sm2_cols.values()),
            names=self.sm2_cols.keys(),
            dtype=str,
            encoding="unicode_escape",
        )
        data_sm2["custodian_price"] = pd.to_numeric(
            data_sm2["custodian_price"], errors="coerce"
        )
        data_sm2["custodian_price"] = data_sm2["custodian_price"].astype(float)
        data_sm2.drop_duplicates(inplace=True)
        return data_sm2

    def read_data(self, dte):
        recon_dte = dtU().get_recon_date(dte)
        rjcs_dte = dtU.get_custodian_date(recon_dte)

        data_sr = self.read_data_sr(rjcs_dte)
        data_dc = self.read_data_dc(rjcs_dte)
        data_sm2 = self.read_data_sm2(rjcs_dte)
        data = pd.concat([data_sr, data_dc])
        data = pd.merge(data, data_sm2, on="raw_instrument", how="left")
        data["date"] = pd.to_datetime(rjcs_dte)
        return data

    def set_cash_currency(self, custodian_df):
        custodian_df.replace({"raw_instrument": self.cash_currency}, inplace=True)
        return custodian_df

    def process_data(self, df):
        df = self.set_cash_currency(df)
        df.rename(
            columns={
                "qty": "custodian_units",
                "acc_id": "account",
                "raw_instrument": "instrument",
            },
            inplace=True,
        )
        df.loc[
            df["instrument"].isin(SUPPORTED_CURRENCIES),
            ["custodian_mv_clean_ac_cad_usd", "custodian_bv_ac_cad_usd"],
        ] = df["custodian_units"]
        df.loc[df["instrument"].isin(SUPPORTED_CURRENCIES), "custodian_price"] = 1
        return df[self.custodian_return_cols]

    def get_custdn_data(self, dte) -> pd.DataFrame:
        df = self.read_data(dte)
        res = self.process_data(df)
        return res
