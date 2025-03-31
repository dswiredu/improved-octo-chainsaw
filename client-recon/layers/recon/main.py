import logging
import warnings

import pandas as pd

from layers.recon import custodian_reconciliation, outlier_detection
from layers.recon.exceptions import FirmNotConfiguredException

warnings.filterwarnings("ignore", category=RuntimeWarning)

logger = logging.getLogger(__name__)


class MainValidation:
    def __init__(self, environment: str) -> None:
        logger.info("Reading config...")
        self.environment = environment
        self.client_config = self.get_client_config()
        self.configured_clients = set(self.client_config["name"])
        self.custodian_metric_map = self.custodian_config.to_dict()["metrics"]

    @property
    def custodian_config(self):
        config = pd.read_csv(
            f"{self.config_path}/custodian_config.csv", index_col="custodian"
        )
        return config

    @property
    def custodian_aliases(self):
        aliases = pd.read_csv(
            f"{self.config_path}/custodian_aliases.csv", index_col="client-name"
        )
        return aliases.to_dict()["recon-alias"]

    @property
    def config_path(self):
        if self.environment in ["nbinproduction", "nbinstaging"]:
            return "s3://d1g1t-nbin-client-configs-ca-central-1/d1ops"
        else:
            return "s3://d1g1t-client-configs-ca-central-1/d1ops"

    def _is_configured(self, client: str) -> bool:
        return client in self.configured_clients

    def get_client_config(self):
        config = pd.read_csv(
            f"{self.config_path}/client_recon_config_{self.environment}.csv"
        )
        for col in [
            "column_name_overwrite",
            "final_output_column_drops",
            "slack_report_exceptions_only",
            "slack_report_metrics_overwrite",
            "threshold_settings",
            "additional_output_columns",
            "recon_funds",
        ]:
            config[col].fillna("", inplace=True)
        return config

    def get_client_info(self, firm: str, client: str):
        if self._is_configured(firm):
            client_row = self.client_config.query("name == @firm")
            client_row_dict = client_row.to_dict("records")[0]
            for path in ["d1g1t_input_file_path"]:
                client_row_dict[path] = client_row_dict[path].replace(firm, client)
            return client_row_dict
        else:
            msg = f"Could not find {firm} firm info in configuration file!"
            raise FirmNotConfiguredException(msg)

    def run_client_validation(
        self,
        firm: str,
        client: str,
        client_version: str,
        dte: str,
        reporting_currency: str,
    ) -> None:
        client_info = self.get_client_info(firm, client)
        output_file_name = custodian_reconciliation.run(
            firm,
            client,
            dte,
            self.environment,
            client_version,
            client_info,
            self.custodian_metric_map,
            reporting_currency,
            self.custodian_aliases,
        )
        if client_info.get(
            "run_outlier_detection", False
        ):  # Remove get once added to added to config
            outlier_detection.run(
                firm,
                client,
                dte,
                self.environment,
                client_version,
                client_info,
                reporting_currency,
                self.custodian_aliases,
                outlier_type="market_value",
            )
            outlier_detection.run(
                firm,
                client,
                dte,
                self.environment,
                client_version,
                client_info,
                reporting_currency,
                self.custodian_aliases,
                outlier_type="return",
            )
        return output_file_name


def recon_main(
    firm: str,
    client: str,
    date: str,
    environment: str,
    client_version: str,
    client_reporting_currency: str,
):
    runner = MainValidation(environment)
    output_file_name = runner.run_client_validation(
        firm=firm,
        client=client,
        client_version=client_version,
        dte=date,
        reporting_currency=client_reporting_currency,
    )
    return output_file_name
