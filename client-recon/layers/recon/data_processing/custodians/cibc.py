import pandas as pd
import logging
import re

from layers.recon.datehandler import DateUtils as dtU
from layers.recon.data_processing.custodians.custodian import Custodian
from layers.recon.exceptions import ClientDataNotFoundException
from layers.recon.utils import get_file_by_prefix

logger = logging.getLogger(__name__)


class CIBC(Custodian):
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

        self.cibc_account_id_mapper = {
            "GWDF10010002": 139528,
            "GWDF20010002": 139530,
        }

        self.bucket_name = "d1g1t-production-file-transfer-ca-central-1"

        self.cibc_mapper = {
            "holdings": {
                "column_mapper": {
                    "Account Number": "account",
                    "As Of Date": "date",
                    "CUSIP CINS": "CUSIP",
                    "Units": "custodian_units",
                    "Market Value Local": "custodian_mv_clean",
                    "Accrued Interest Local": "custodian_ai",
                    "Local Price": "custodian_price",
                    "Local Currency Code": "currency",
                },
                "numeric_fields_map": (
                    "Units",
                    "Market Value Local",
                    "Accrued Interest Local",
                    "Local Price",
                ),
                "file_prefix": f"bnymellon/{self.firm}/Custody_Valuation_",
            },
            "cash": {
                "column_mapper": {
                    "Cash Account Number": "account",
                    "Local Currency Code": "instrument",
                    "Ending Balance Local": "custodian_units",
                },
                "numeric_fields_map": ("Ending Balance Local",),
                "file_prefix": f"bnymellon/{self.firm}/Settled_Cash_Balances_",
            },
        }

    def clean_numeric(self, value):
        cleaned_value = re.sub(r"[^\d.-]", "", str(value))
        return pd.to_numeric(cleaned_value, errors="coerce")

    def process_holding_data(self, holdings_data: pd.DataFrame) -> pd.DataFrame:
        holdings_data["instrument"] = (
            "CIBC_"
            + holdings_data["currency"]
            + "_"
            + holdings_data["CUSIP"].astype(str)
        )
        holdings_data["account"] = holdings_data["account"].astype(str)
        holdings_data = holdings_data.dropna(subset=["account"])
        return holdings_data

    def process_cash_data(self, cash_data: pd.DataFrame) -> pd.DataFrame:
        cash_data["custodian_mv_clean"] = cash_data["custodian_units"]
        cash_data["custodian_price"] = 1
        cash_data["date"] = cash_data["As Of Date"]
        cash_data["account"] = cash_data["account"].astype(str).str[:6]
        return cash_data

    def read_cibc_file(self, cibc_dte, file_type):
        file = get_file_by_prefix(
            cibc_dte, self.bucket_name, self.cibc_mapper[file_type]["file_prefix"]
        )
        numeric_fields = self.cibc_mapper[file_type]["numeric_fields_map"]

        if file:
            data = pd.read_csv(
                "s3://d1g1t-production-file-transfer-ca-central-1/" + file,
                encoding="ISO-8859-1",
                converters={field: self.clean_numeric for field in numeric_fields},
                usecols=list(self.cibc_mapper[file_type]["column_mapper"].keys()),
            )
            data["As Of Date"] = pd.to_datetime(cibc_dte)
            return data.rename(columns=self.cibc_mapper[file_type]["column_mapper"])

        else:
            msg = (
                f"Could not find {file_type} file for {self.firm} at "
                f"{self.cibc_mapper[file_type]['file_prefix']}!"
            )
            raise ClientDataNotFoundException(msg)

    def read_data(self, date: str) -> pd.DataFrame:
        recon_dte = dtU().get_recon_date(date)
        cibc_dte = dtU.get_custodian_date(recon_dte)
        holdings_data = self.read_cibc_file(cibc_dte, "holdings")
        cash_data = self.read_cibc_file(cibc_dte, "cash")
        return holdings_data, cash_data

    def process_data(
        self, holdings_data: pd.DataFrame, cash_data: pd.DataFrame
    ) -> pd.DataFrame:
        holdings_data_processed = self.process_holding_data(holdings_data)
        cash_data_processed = self.process_cash_data(cash_data)
        cibc_data = pd.concat([holdings_data_processed, cash_data_processed])
        return cibc_data

    def get_custdn_data(self, dte) -> pd.DataFrame:
        holdings_data, cash_data = self.read_data(dte)
        res = self.process_data(holdings_data, cash_data)
        return res
