"""
Script to demonstrate interacting with d1g1t api.

Sample Usage:
    python simple_script.py --server https://api-claret.d1g1t.com
                            -u david.wiredu@d1g1t.com
                            -p trend-aum.json
                            -c trend-aum
"""

import logging
import os

from utils import get_json
from ps.base import PSMain
from ps.parser import ChartTableFormatter
from exceptions import InputValidationError

LOG = logging.getLogger(__name__)

CALCULATION_ENDPOINTS = [
    "trend-aum",
    "cph-table",
    "log-details",
    "tax-lot-unrealized-gains-n-losses",
]

DATA_ENDPOINTS = [
    "households",
    "investment-mandates",
    "accounts",
]


class SimpleCalc(PSMain):
    def __init__(self):
        super().__init__()

    def add_extra_args(self):
        self.parser.add_argument(
            "-p",
            "--payload-file",
            type=str,
            help="Payload filename stored in data folder.",
            required=False,
        )

        self.parser.add_argument(
            "-c",
            "--calculation-endpoint",
            help="Calculation endpoint. To be used with --payload-file parameter",
            default=None,
            choices=CALCULATION_ENDPOINTS,
        )

        self.parser.add_argument(
            "-d",
            "--data-endpoint",
            default=None,
            choices=DATA_ENDPOINTS,
            help="Data endpoint.",
        )

    @property
    def payload(self):
        LOG.info("Getting payload...")
        payload_path = os.path.join("data", self.args.payload_file)
        return get_json(path=payload_path)

    def run_calc(self):
        LOG.info("Running calculation...")
        calc = self.args.calculation_endpoint
        resp = self.get_calculation(calc, self.payload)
        parser = ChartTableFormatter(resp, self.payload)
        res = parser.parse_data()
        res.to_csv(f"{calc}.csv", index=False)
        LOG.info("-" * 30)

    def get_client_data(self):
        endpoint = self.args.data_endpoint
        LOG.info(f"Getting data from {endpoint}")
        df = self.get_data(endpoint)
        df.to_csv(f"{endpoint}.csv", index=False)
        LOG.info("-" * 30)

    def after_login(self):
        if self.args.calculation_endpoint and self.args.payload_file:
            self.run_calc()
        elif self.args.data_endpoint:
            self.get_client_data()
        else:
            raise InputValidationError("Invalid arguments!")


if __name__ == "__main__":
    work = SimpleCalc()
    work.main()
