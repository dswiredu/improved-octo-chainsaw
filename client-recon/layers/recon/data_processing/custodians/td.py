import pandas as pd
import logging
import datetime

from layers.recon.data_processing.custodians.custodian import Custodian
from layers.recon.datehandler import DateUtils, STD_DATE_FORMAT
from layers.recon.exceptions import InputValidationException
from layers.recon.exceptions import ClientDataNotFoundException

logger = logging.getLogger(__name__)


class TD(Custodian):
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
        self.position_col_map = {
            "Acct ID": "account",
            "CUSIP": "instrument",
            "T/D Qty": "custodian_units",
            "Mkt Price": "custodian_prices",
            "Ccy": "currency",
            "Mkt Value $CAD": "custodian_mv_dirty",
        }
        self.cash_col_map = {
            "Acct ID": "account",
            "Ccy": "instrument",
            "T/D Balance": "custodian_units",
        }

    @property
    def get_feed_path(self) -> str:
        return f"s3://d1g1t-custodian-data-{self.region}-central-1/{self.custodian}/{self.feed}"

    def read_position_data(self, file_date: str):
        s3_file_position = f"{self.feed_path}/{file_date}/Positions.csv"
        try:
            df = pd.read_csv(
                s3_file_position,
                usecols=self.position_col_map.keys(),
            )
            df.rename(columns=self.position_col_map, inplace=True)
            return df
        except FileNotFoundError:
            msg = f"Could not find Position file for {self.firm} at {s3_file_position}!"
            raise ClientDataNotFoundException(msg)

    def read_cash_data(self, file_date: str):
        s3_file_cash = f"{self.feed_path}/{file_date}/Account_Summary.csv"
        try:
            df = pd.read_csv(
                s3_file_cash,
                usecols=self.cash_col_map.keys(),
            )
            df["custodian_prices"] = 1
            df["custodian_mv_dirty"] = -df["T/D Balance"]
            df["T/D Balance"] = -df["T/D Balance"]
            df["currency"] = df["Ccy"]
            df.dropna(subset=["Acct ID", "Ccy"], inplace=True)
            df = df[df["Acct ID"] != "GRAND TOTAL:"]
            df.rename(columns=self.cash_col_map, inplace=True)
            return df
        except FileNotFoundError:
            msg = f"Could not find cash file for {self.firm} at {s3_file_cash}!"
            raise ClientDataNotFoundException(msg)

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

        file_date = self.adjust_date_for_td_files(tday)
        position = self.read_position_data(file_date)
        cash = self.read_cash_data(file_date)
        data = pd.concat([position, cash])
        data["date"] = pd.to_datetime(file_date)
        return data

    def adjust_date_for_td_files(self, date):
        today = datetime.datetime.today().date()
        as_of_date = datetime.datetime.strptime(date, STD_DATE_FORMAT)
        if today.weekday() == 5:  # Saturday -> move to Friday
            as_of_date = as_of_date - datetime.timedelta(days=1)
        as_of_date = DateUtils.get_custodian_date(as_of_date)
        return as_of_date

    def process_data(self, df):
        return df

    def get_custdn_data(self, dte) -> pd.DataFrame:
        df = self.read_data(dte)
        res = self.process_data(df)
        return res
