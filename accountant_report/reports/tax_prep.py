import logging

import pandas as pd
from openpyxl.utils.dataframe import dataframe_to_rows

from claret.accountant_report.main import AccountantReport

LOG = logging.getLogger(__name__)


class TaxPrepReport:
    """Class to generate Tax Prep reports."""

    def __init__(self, report: AccountantReport, report_type: str):
        self.report = report
        self.report_type = report_type
        self.account_info = report.account_info
        self.output_location = report.output_location
        self.start_date = report.start_date
        self.end_date = report.end_date
        self.report_headers = ["[|0|1]", ""]
        self.report_sheet = self.report._workbook.create_sheet(self.sheet_name)

        self.bond_count = 1
        self.stock_count = 1
        self.output_rows = []

    @property
    def field_map(self) -> dict:
        mapp = {
            "capital": {
                "A1": "Quantity",
                "A2": "Description",
                "A5": "Asset Account Local",
                "A6": "Cash Account Local",
            },
            "income": {
                "A1": "Description",
                "A7": "d1g1t Transaction Amount (Gross - Trx Currency)",
                "A11": "d1g1t Transaction Amount (Gross - Trx Currency)",
                "A12": "FX Rate",
            },
        }
        return mapp[self.report_type]

    @property
    def sheet_name(self) -> str:
        mapp = {"capital": "Taxprep - Schedule 6", "income": "Taxprep - Schedule 3"}
        return mapp[self.report_type]

    @property
    def bond_text(self):
        mapp = {
            "capital": f"FDCAP.SLIPC[{self.bond_count}].Ttwcap",
            "income": f"FDDIV.SLIPA[{self.bond_count}].Ttwcap",
        }
        return mapp[self.report_type]

    @property
    def stock_text(self):
        mapp = {
            "capital": f"FDCAP.SLIPA[{self.stock_count}].Ttwcap",
            "income": f"FDDIV.SLIPA[{self.stock_count}].Ttwcap",
        }
        return mapp[self.report_type]

    @property
    def date_field(self):
        return "Settle date" if self.report_type == "income" else "Settle Date"

    def set_instrument_count(self, is_equity: bool) -> None:
        if is_equity:
            self.stock_count += 1
        else:
            self.bond_count += 1

    def get_taxprep_row(self, row: pd.Series, field_map: dict) -> list:
        is_equity = row["is_equity"] if self.report_type == "capital" else True
        prefix = self.stock_text if is_equity else self.bond_text

        for key, value in field_map.items():
            self.output_rows.append([f"{prefix}{key}", row[value]])

        if self.report_type == "capital":
            last_value = "X" if row["is_cad"] else ""
            self.output_rows.append([f"{prefix}{key}", last_value])
        self.set_instrument_count(is_equity)

    def get_taxprep_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        For capital : (PT) :I believe it should be all closing transactions. However, the amounts used should be in account reporting currency.
        For Income : (PT) : Rows populated here are Income transactions filtered for 1. Country is "Canada", 2. Symbol2 == 'divinc' (i.e Security ID of -2 transaction)
        """
        if self.report_type == "capital":
            currency_idx = df["transaction_currency"] == self.account_info["reporting_currency_name"]
            sell_idx = df["d1g1t Transaction Type"] == "Sell"
            df["is_equity"] = df["Security Type"] == "Equity"
            df["is_cad"] = df["Security Asset Class"].str.contains("Canad")
            filter_rule = currency_idx & sell_idx
        elif self.report_type == "income":
            country_idx = df["Country"] == "Canada"  # strictly
            divinc_idx = df["Security ID2"].str.endswith("divinc")
            filter_rule = country_idx & divinc_idx
        res = df[filter_rule].sort_values(by=[self.date_field])
        return res

    def generate_worksheet(self, df: pd.DataFrame) -> None:
        sheet = self.report_sheet
        sheet["A1"] = "[|0|1]"

        for row in dataframe_to_rows(df, index=False, header=False):
            sheet.append(row)

    def run(self, frame: pd.DataFrame) -> None:
        df = self.get_taxprep_frame(frame)
        if not df.empty:
            field_map = self.field_map
            for _, row in df.iterrows():
                self.get_taxprep_row(row, field_map)
            res = pd.DataFrame(self.output_rows, columns=self.report_headers)
            self.generate_worksheet(res)
