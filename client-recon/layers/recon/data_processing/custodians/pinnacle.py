import pandas as pd
import logging
import datetime

from layers.recon.data_processing.custodians.custodian import Custodian
from layers.recon.datehandler import DateUtils, STD_DATE_FORMAT
from layers.recon.exceptions import InputValidationException

logger = logging.getLogger(__name__)


class Pinnacle(Custodian):
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

        self.se_cols = [
            "acc_id",
            "current_qty",
            "safekeeping_qty",
            "pending_qty",
            "book_value",
            "raw_instrument",
        ]

        self.cl_cols = ["acc_id", "qty"]

        self.ac_cols = ["acc_id", "raw_instrument"]

        self.sm_cols = ["raw_instrument", "uom"]

        self.qty_cols = ["current_qty", "safekeeping_qty", "pending_qty"]

        self.cash_currency = {"C": "CAD", "U": "USD"}

        """
        Pinnacle has different middle file name for different clients - we store them in a file on FTP
        """
        self.extension_file = pd.read_csv(
            "s3://d1g1t-custodian-data-ca/pinnacle/mapping-rules/pinnacle_file_extensions.csv"
        )

    def read_data_se(self, file_date: str):
        """
        read data from one of the input file - se file
        output: dataframe from se
        """
        extension = self.get_client_extension(self.firm)
        s3_file_se = f"{self.feed_path}/{file_date}/se{extension}{file_date[2:8]}"
        data_se = pd.read_fwf(
            s3_file_se,
            colspecs=[(0, 8), (25, 39), (40, 54), (55, 69), (128, 143), (176, 185)],
            names=self.se_cols,
            dtype="str",
        )

        for col in self.qty_cols:
            data_se[col] = data_se[col].astype(float)
        data_se["qty"] = data_se[self.qty_cols].sum(axis=1)
        return data_se

    def read_data_cl(self, file_date: str):
        """
        read data from one of the input file - cl file (cash balances)
        output: dataframe from cl
        """
        extension = self.get_client_extension(self.firm)
        s3_file_cl = f"{self.feed_path}/{file_date}/cl{extension}{file_date[2:8]}"

        data_cl = pd.read_fwf(
            s3_file_cl,
            colspecs=[(0, 8), (22, 35)],
            names=self.cl_cols,
            dtype="str",
        )

        data_cl["qty"] = pd.to_numeric(data_cl["qty"], errors="coerce").astype(float)
        data_cl["qty"] = (-1) * (data_cl["qty"])
        return data_cl

    def read_data_ac(self, file_date: str):
        """
        read data from one of the input file - ac file (currency)
        output: dataframe from ac
        """
        extension = self.get_client_extension(self.firm)
        s3_file_ac = f"{self.feed_path}/{file_date}/ac{extension}{file_date[2:8]}"

        data_ac = pd.read_fwf(
            s3_file_ac,
            colspecs=[(4, 12), (20, 22)],
            names=self.ac_cols,
            dtype="str",
        )

        data_ac.drop_duplicates(inplace=True)
        return data_ac

    def read_data_sm(self, file_date: str):
        """
        read data from one of the input file - sm file (scale positions)
        output: dataframe from sm
        """
        extension = self.get_client_extension(self.firm)
        s3_file_sm = f"{self.feed_path}/{file_date}/sm{extension}{file_date[2:8]}"

        data_sm = pd.read_fwf(
            s3_file_sm,
            colspecs=[(111, 119), (100, 110)],
            names=self.sm_cols,
            dtype="str",
            encoding="unicode_escape",
        )

        data_sm["uom"] = data_sm["uom"].astype(float)
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

        data_se = self.read_data_se(file_date)
        data_cl = self.read_data_cl(file_date)
        data_ac = self.read_data_ac(file_date)
        data_sm = self.read_data_sm(file_date)
        data_cl_merged = data_cl.merge(data_ac, on="acc_id", how="left")
        data = pd.concat([data_se, data_cl_merged])
        data = pd.merge(data, data_sm, on="raw_instrument", how="left")
        data["date"] = pd.to_datetime(file_date)
        return data

    def set_cash_currency(self, custodian_df):
        custodian_df.replace({"raw_instrument": self.cash_currency}, inplace=True)
        return custodian_df

    def get_client_extension(self, firm: str):
        client_extension = dict(
            zip(self.extension_file.name, self.extension_file.extension)
        )
        return client_extension[firm]

    def process_data(self, df):
        df = self.set_cash_currency(df)
        df["custodian_units"] = df["qty"]
        df.rename(
            columns={"acc_id": "account", "raw_instrument": "instrument"},
            inplace=True,
        )
        df["custodian_units"] = df["custodian_units"].astype(float)

        return df[self.custodian_return_cols]

    def get_custdn_data(self, dte) -> pd.DataFrame:
        df = self.read_data(dte)
        res = self.process_data(df)
        return res
