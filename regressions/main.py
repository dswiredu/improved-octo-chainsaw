"""
Script to run regressions for data saved between two environments.

Supported data: net-asset-value-history, trend-aum, trend-cumulative return, quantity and market value.

Usage:
    python -m support_tools.run_regressions
                            -b bbr-staging
                            -c gamma-us-staging
                            -bloc s3://d1g1t-client-us/bbr/python-apps-tests/bbr-staging/
                            -cloc s3://d1g1t-client-us/bbr/python-apps-tests/gamma-us-staging/
                            -r trend-aum
                            -o s3://d1g1t-client-us/bbr/python-apps-tests/regression-results
"""
import argparse
from datetime import datetime
import logging
import os
import pathlib

import awswrangler as wr
import pandas as pd
from utils import get_json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REGRESSION_TYPES = [
    "net-asset-value-history",
    "trend-aum",
    "trend-cumul-ret",
    "quantity-mv",
    "summary-single",
    "bbr-compare",
]


class Regression:
    """Regression class."""

    def __init__(self):
        """Class initializer."""
        self.args = self.get_args()
        self.regression_type = self.args.regression_type
        self.base_client = self.args.base_client
        self.compare_client = self.args.comparison_client
        self.threshold = self.args.threshold
        self.regression_map = self.get_regression_map()
        self.recon_metrics = self.regression_map["metrics"]
        self.merge_columns = self.regression_map["merge_columns"]
        self.date_col = self.regression_map.get("date_col")
        self.output_file = self.get_regression_outputfile()

    @property
    def regression_mapping_file(self):
        """Get regression mappings file stored in internal/data."""
        dir_path = pathlib.Path(__file__).parent.resolve()
        return os.path.join(dir_path, "..", "data", "regression-mappings.json")

    def get_regression_map(self) -> dict:
        """Get regression mappings for provided regression type."""
        mappings = get_json(path=self.regression_mapping_file)
        return mappings.get(self.regression_type, mappings["default"])

    @staticmethod
    def _valid_s3_path(path: str):
        """Determine if path is (s3) valid."""
        if path.startswith("s3"):
            return path
        msg = f"Not a valid s3 path format: {path}"
        raise argparse.ArgumentTypeError(msg)

    def get_args(self):
        """Get command-line arguments."""
        parser = argparse.ArgumentParser(
            description="Script to run regressions for data stored on s3 for REGRESSION_TYPES.",
        )

        parser.add_argument(
            "-b",
            "--base-client",
            type=str,
            help="Base client to compare results with.",
            required=True,
        )

        parser.add_argument(
            "-c",
            "--comparison-client",
            type=str,
            help="Client with results to compare with base client.",
            required=True,
        )

        parser.add_argument(
            "-bloc",
            "--base-client-data-location",
            type=self._valid_s3_path,
            help="s3 location of extracted data for base client.",
            required=True,
        )

        parser.add_argument(
            "-cloc",
            "--comparison-client-data-location",
            type=self._valid_s3_path,
            help="s3 location of extracted data for comparison client.",
            required=True,
        )

        parser.add_argument(
            "-r",
            "--regression-type",
            type=str,
            choices=REGRESSION_TYPES,
            help="The type of data we are running regressions on.",
            required=True,
        )

        parser.add_argument("-t", "--threshold", type=float, default=0.0001, help="Regression threshold.")
        parser.add_argument(
            "-o",
            "--regression-output-location",
            type=str,
            help="Location to export regression results.",
            required=True,
        )
        return parser.parse_args()

    def read_data(self, location: str, client: str):
        """Read all files into a single dataframe from s3 location."""
        files = wr.s3.list_objects(location)
        if files:
            df = wr.s3.read_csv(files, dtype={x: str for x in self.regression_map["str_cols"]})

            if self.regression_type == "net-asset-value-history":
                df = df[df.Date != "MtD"]
            if self.date_col:
                df[self.date_col] = pd.to_datetime(df[self.date_col])

            metric_cols = [x for x in df.columns if x not in self.merge_columns]
            metric_rename_cols = {x: f"{x}_{client}" for x in metric_cols}
            df.rename(columns=metric_rename_cols, inplace=True)
            return df
        raise ValueError(f"No files found in {location}")

    def compare_frames(self, df_left: pd.DataFrame, df_right: pd.DataFrame) -> pd.DataFrame:
        """Compare two dataframes based on merge columns."""
        res = pd.merge(df_right, df_left, how="outer", on=self.merge_columns, validate="1:1")
        return res

    def _metric_recon_columns(self, metric: str) -> list:
        """Get list of columns to return for a specific metric."""
        return [
            f"{metric}_{self.base_client}",
            f"{metric}_{self.compare_client}",
            f"{metric}_diff",
            f"{metric}_reconciled",
        ]

    @property
    def recon_return_columns(self):
        """Get the full set of columns returned in regression dataframe."""
        metric_return_cols = [self._metric_recon_columns(metric) for metric in self.recon_metrics]
        return self.merge_columns + sum(metric_return_cols, [])

    def apply_recon_rules(self, left: pd.Series, right: pd.Series, dif: pd.Series) -> pd.Series:
        """Get column that specifies whether numbers are reconcilied based on a threshold."""
        res = dif.abs() <= self.threshold
        true_idx = (left.fillna(0) - right.fillna(0)).abs() <= self.threshold
        res.loc[true_idx] = True
        return res

    def reconcile_metrics(self, df: pd.DataFrame) -> None:
        """Apply recon rules to each set of columns per metric."""
        for metric in self.recon_metrics:
            left, right = df[f"{metric}_{self.base_client}"], df[f"{metric}_{self.compare_client}"]
            df[f"{metric}_diff"] = left - right
            dif = df[f"{metric}_diff"]
            df[f"{metric}_reconciled"] = self.apply_recon_rules(left, right, dif)

    def get_regression_outputfile(self):
        """Get filepath used to save regression results."""
        today = datetime.today().strftime("%Y-%m-%d")
        return f"{self.args.regression_output_location}/{self.regression_type}_regression_{today}.csv"

    def run(self):
        """Run regressions."""
        logger.info("Reading input data....")
        base_df = self.read_data(self.args.base_client_data_location, self.base_client)
        compare_df = self.read_data(self.args.comparison_client_data_location, self.compare_client)

        accounts = set(compare_df.firm_provided_key)
        base_df = base_df[base_df.firm_provided_key.isin(accounts)]

        logger.info("Comparing frames....")
        res = self.compare_frames(base_df, compare_df)

        logger.info("Reconciling data...")
        self.reconcile_metrics(res)

        res = res[self.recon_return_columns]

        logger.info(f"Saving regression results to {self.output_file}...")
        res.to_csv(self.output_file, index=False)


if __name__ == "__main__":
    regression = Regression()
    regression.run()
