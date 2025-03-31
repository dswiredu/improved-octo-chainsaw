import pandas as pd
import logging
import datetime

from layers.recon.data_processing.custodians.custodian import Custodian
from layers.recon.datehandler import DateUtils, STD_DATE_FORMAT
from layers.recon.exceptions import InputValidationException

logger = logging.getLogger(__name__)


class Fidelity(Custodian):
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

        self.pas_clients = [
            "oceanfront",
            "verecan",
            "delisle",
            "fwp",
            "harness",
            "milestone",
            "origin",
            "samara",
            "westmount",
        ]

        self.sr_cols = {
            "cusip": (3, 12),
            "acc_id": (12, 20),
            "current_qty": (66, 82),
            "sfk_qty": (82, 98),
            "pending_qty": (98, 114),
            "custodian_bv_ac_cad_usd": (178, 194),
            "offbook_qty": (
                (276, 291) if self.client in self.pas_clients else (264, 280)
            ),
            "custodian_mv_bid_price": (146, 161),
            "custodian_acb": (217, 233),
        }

        self.dc_cols = {
            "acc_id": (3, 11),
            "acc_currency": (21, 22),
            "cash_balance": (95, 109),
        }

        self.sm_cols = {
            "raw_instrument": (3, 12),
            "custodian_bid_price": (50, 69),
            "custodian_ask_price": (69, 88),
            "custodian_last_price": (88, 107),
        }

        self.sm2_cols = {
            "raw_instrument": (110, 119),
            "uom": (99, 110),
            "custodian_price": (132, 143),
        }

        self.process_return_columns = [
            "date",
            "account",
            "instrument",
            "custodian_units",
        ]

        """
        Access has different file extension for different clients - we store them in a file on FTP
        """
        self.extension_file = pd.read_csv(
            "s3://d1g1t-custodian-data-ca/fidelity/mapping-rules/fidelity_file_extensions.csv"
        )

        self.currency_map = self.get_currency_map()

    def transform_number_sec(self, df: pd.DataFrame, qty_type) -> float:
        """
        special logic for fidelity to transform cash/security and identify if it is a positive nuumber
        input: number that need to be transferred and type of the number - either cash or sec
        output: transferred number
        """
        res = df[qty_type].copy()
        idx = res.str[-1] == "-"
        res[idx] = "-" + res[idx].str[:-1]
        res = pd.to_numeric(res, errors="coerce")
        if qty_type == "custodian_mv_bid_price":
            res = res * 100
        if qty_type in [
            "custodian_bid_price",
            "custodian_last_price",
            "custodian_ask_price",
        ]:
            res = res / 100000000
        if qty_type in [
            "custodian_bv_ac_cad_usd",
            "custodian_acb",
        ]:
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
        extension = self.get_client_extension(self.feed)
        s3_file_sr = f"{self.feed_path}/{file_date}/sr{file_date[2:8]}.{extension}"
        data_sr = pd.read_fwf(
            s3_file_sr,
            colspecs=list(self.sr_cols.values()),
            names=self.sr_cols.keys(),
            dtype=str,
        )

        data_sr["custodian_mv_bid_price"] = self.transform_number_sec(
            data_sr, "custodian_mv_bid_price"
        )
        data_sr["custodian_bv_ac_cad_usd"] = self.transform_number_sec(
            data_sr, "custodian_bv_ac_cad_usd"
        )
        data_sr["current_qty"] = self.transform_number_sec(data_sr, "current_qty")
        data_sr["pending_qty"] = self.transform_number_sec(data_sr, "pending_qty")
        data_sr["sfk_qty"] = self.transform_number_sec(data_sr, "sfk_qty")
        data_sr["offbook_qty"] = self.transform_number_sec(data_sr, "offbook_qty")
        data_sr["current_qty"] = (
            data_sr["pending_qty"].fillna(0)
            + data_sr["current_qty"].fillna(0)
            + data_sr["sfk_qty"].fillna(0)
            + data_sr["offbook_qty"].fillna(0)
        )
        data_sr["custodian_acb"] = self.transform_number_sec(data_sr, "custodian_acb")
        data_sr.rename(
            columns={"cusip": "raw_instrument", "current_qty": "qty"}, inplace=True
        )
        return data_sr

    def read_data_dc(self, file_date: str):
        """
        read data from one of the input file - dc file (cash balances)
        output: dataframe from dc
        """
        extension = self.get_client_extension(self.feed)
        s3_file_dc = f"{self.feed_path}/{file_date}/dc{file_date[2:8]}.{extension}"

        data_dc = pd.read_fwf(
            s3_file_dc,
            colspecs=list(self.dc_cols.values()),
            names=self.dc_cols.keys(),
            dtype="str",
        )

        data_dc["cash_balance"] = self.transform_number_cash(data_dc)

        data_dc.rename(
            columns={"acc_currency": "raw_instrument", "cash_balance": "qty"},
            inplace=True,
        )
        return data_dc

    def read_data_sm2(self, file_date: str):
        """
        read data from one of the input file - sm2 file (scale positions)
        output: dataframe from sm2
        """
        s3_file_sm2 = f"{self.feed_path}/{file_date}/sm2{file_date[2:8]}.fid"

        data_sm2 = pd.read_fwf(
            s3_file_sm2,
            colspecs=list(self.sm2_cols.values()),
            names=self.sm2_cols.keys(),
            dtype="str",
            encoding="unicode_escape",
        )

        data_sm2["uom"] = data_sm2["uom"].astype(float)
        data_sm2["custodian_price"] = pd.to_numeric(
            data_sm2["custodian_price"], errors="coerce"
        ).astype("float64")
        data_sm2.drop_duplicates(inplace=True)
        return data_sm2

    def read_data_sm(self, file_date: str):
        """
        read data from one of the input file - sm file (prices)
        output: dataframe from sm
        """
        s3_file_sm = f"{self.feed_path}/{file_date}/sm{file_date[2:8]}"

        data_sm = pd.read_fwf(
            s3_file_sm,
            colspecs=list(self.sm_cols.values()),
            names=self.sm_cols.keys(),
            dtype="str",
            encoding="unicode_escape",
        )

        data_sm["custodian_bid_price"] = self.transform_number_sec(
            data_sm, "custodian_bid_price"
        )
        data_sm["custodian_ask_price"] = self.transform_number_sec(
            data_sm, "custodian_ask_price"
        )
        data_sm["custodian_last_price"] = self.transform_number_sec(
            data_sm, "custodian_last_price"
        )
        data_sm.drop_duplicates(inplace=True)
        return data_sm

    def read_data(self, dte):
        """ """
        logger.info(
            f"Retrieving custodian data from {self.feed_path} for {self.firm}.."
        )
        if not dte:
            tday = DateUtils.get_last_cob_date()
        elif DateUtils.is_valid_date_input(dte):
            tday = dte
        else:
            msg = f"The input {dte} is incorrect! Expected YYYY-MM-DD"
            raise InputValidationException(msg)

        tday = datetime.datetime.strptime(tday, STD_DATE_FORMAT)
        file_date = DateUtils.get_custodian_date(tday)

        data_sr = self.read_data_sr(file_date)
        data_dc = self.read_data_dc(file_date)
        data_sm2 = self.read_data_sm2(file_date)
        data_sm = self.read_data_sm(file_date)
        data = pd.concat([data_sr, data_dc])
        data = pd.merge(data, data_sm2, on="raw_instrument", how="left")
        data = pd.merge(data, data_sm, on="raw_instrument", how="left")
        data["date"] = pd.to_datetime(file_date)
        return data

    def set_cash_currency(self, custodian_df):
        custodian_df.replace({"raw_instrument": self.currency_map}, inplace=True)
        return custodian_df

    def get_client_extension(self, client: str):
        client_extension = dict(
            zip(self.extension_file.name, self.extension_file.extension)
        )
        return client_extension[client]

    def get_currency_map(self) -> dict:
        return (
            pd.read_csv(
                "s3://d1g1t-custodian-data-ca/fidelity/mapping-rules/fidelity_currency.csv"
            )
            .set_index("character")["currency"]
            .to_dict()
        )

    def process_data(self, df):
        df = self.set_cash_currency(df)
        df["scaled_qty"] = df["qty"]
        df.rename(
            columns={
                "scaled_qty": "custodian_units",
                "acc_id": "account",
                "raw_instrument": "instrument",
            },
            inplace=True,
        )
        df.loc[
            df["instrument"].isin(self.currency_map.values()),
            ["custodian_mv_clean", "custodian_bv_ac_cad_usd"],
        ] = df["qty"]

        df.loc[
            df["instrument"].isin(self.currency_map.values()),
            [
                "custodian_price",
                "custodian_bid_price",
                "custodian_last_price",
                "custodian_ask_price",
                "custodian_acb",
            ],
        ] = 1
        df["uom"] = df["uom"].fillna(1)
        df["custodian_mv_clean"] = (
            df["custodian_units"] * df["custodian_price"] * df["uom"]
        )
        return df

    def get_custdn_data(self, dte) -> pd.DataFrame:
        df = self.read_data(dte)
        res = self.process_data(df)
        return res
