import pandas as pd
import logging
import datetime

from layers.recon.data_processing.custodians.custodian import Custodian
from layers.recon.datehandler import DateUtils, STD_DATE_FORMAT
from layers.recon.exceptions import InputValidationException

logger = logging.getLogger(__name__)


class Pershing(Custodian):
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

        self.ecmb_cols = {
            "instrument": (55, 59),
            "account": (11, 20),
            "custodian_units": (98, 117),
        }

        self.gcus_cols = {
            "instrument": (21, 30),
            "account": (11, 20),
            "custodian_units": (73, 92),
        }

    def transform_number_with_sign(self, df: pd.DataFrame, column, uom) -> float:
        res = df[column].copy()
        negative_sign_idx = res.str[-1] == "-"
        res[negative_sign_idx] = "-" + res[negative_sign_idx].str[:-1]
        res = pd.to_numeric(
            res.str.replace(r"[^\d.-]", "", regex=True), errors="coerce"
        )
        res = res / uom
        return res

    def read_pershing_data(self, file_date: str, file_type: str):
        columns = getattr(self, f"{file_type.lower()}_cols", None)
        s3_file = f"s3://d1g1t-custodian-data-us-east-1/pershing/{self.client}/{file_date}/{file_type}"
        data = pd.read_fwf(
            s3_file,
            colspecs=list(columns.values()),
            names=columns.keys(),
            skiprows=1,
            skipfooter=1,
            engine="python",
        )
        data["date"] = pd.to_datetime(file_date)
        return data

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

        data_ecmb = self.read_pershing_data(file_date, "ECMB")
        data_gcus = self.read_pershing_data(file_date, "GCUS")

        return data_ecmb, data_gcus

    def process_data_ecmb(self, df_ecmb):
        df_ecmb["custodian_units"] = self.transform_number_with_sign(
            df_ecmb, "custodian_units", 100
        )
        df_ecmb["instrument"] = "MMF" + df_ecmb["instrument"]
        return df_ecmb

    def process_data_gcus(self, df_gcus):
        df_gcus["custodian_units"] = self.transform_number_with_sign(
            df_gcus, "custodian_units", 100000
        )

        return df_gcus

    def process_data(self, df_ecmb, df_gcus):
        processed_data_ecmb = self.process_data_ecmb(df_ecmb)
        processed_data_gcus = self.process_data_gcus(df_gcus)
        df = pd.concat([processed_data_ecmb, processed_data_gcus])
        return df

    def get_custdn_data(self, dte) -> pd.DataFrame:
        df_ecmb, df_gcus = self.read_data(dte)
        processed_data = self.process_data(df_ecmb, df_gcus)
        res = self.apply_firm_specific_logic(processed_data)
        return res
