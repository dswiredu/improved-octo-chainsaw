import logging
from typing import List, Tuple
import warnings

import pandas as pd

import layers.recon.data_processing as dp
from layers.recon.data_processing.d1g1t import get_d1g1t_client_data
from layers.recon.utils import get_ignored_accounts, archive_s3_files
from layers.recon.exceptions import (
    ClientDataNotFoundException,
    CustodianFeedException,
    CustodianMetricException,
    InputValidationException,
    FirmSpecificLogicException,
)
from layers.recon.validation import validate_custodian_data
import layers.recon.data_processing.d1g1t_clients as dc
from layers.recon.reporting import (
    send_recon_summary,
    send_recon_to_spotlight,
    generate_output_file,
    get_recon_output_filename,
    generate_breaking_accounts,
)

warnings.filterwarnings("ignore", category=RuntimeWarning)

logger = logging.getLogger(__name__)


class CustodianValidation:
    def __init__(
        self,
        environment: str,
        client_info: dict,
        custodian_metric_map: dict,
        custodian_aliases: dict,
    ) -> None:
        self.environment = environment
        self.client_info = client_info
        self.custodian_metric_map = custodian_metric_map
        self.custodian_aliases = custodian_aliases
        self.recon_metric_map = {}
        self.custodian_data_error_msg = ""

    @staticmethod
    def get_custodian_n_feed(custdn_feed: str) -> Tuple:
        custodian, feed, region = custdn_feed.split("|")
        return custodian.strip(), feed.strip(), region.strip()

    def get_all_recon_metrics(self, custodian: str) -> list:
        custdoian_metrics_str = self.custodian_metric_map[custodian]
        custodian_metrics = custdoian_metrics_str.split(",")
        client_metrics_str = self.client_info.get("client_metrics")
        if pd.notna(client_metrics_str):
            client_metrics = self.client_info["client_metrics"].split(",")
        else:
            client_metrics = []
        return [x.strip() for x in custodian_metrics + client_metrics]

    @staticmethod
    def __threshold_setting(setting: str) -> List[str]:
        """
        splits a threshold setting into a list.
        :param: setting: string of the form "metric,threshold_type,threshold"
        """
        return [x.strip() for x in setting.split(",")]

    def get_threshold_settings(self, settings_string: str) -> dict:
        if not settings_string:
            return dict()
        try:
            metric_threshold_settings: List[List[str]] = [
                self.__threshold_setting(setting)
                for setting in settings_string.split("|")
            ]
            threshold_settings_dict = {
                metric: {
                    "threshold_type": threshold_type,
                    "threshold": float(threshold),
                }
                for [metric, threshold_type, threshold] in metric_threshold_settings
            }
            return threshold_settings_dict
        except ValueError:
            msg = "Threshold settings are incorrect. Correct format is: metric,threshold_type,threshold|..."
            raise InputValidationException(msg)

    @staticmethod
    def get_additional_columns(cols: str) -> List[str]:
        if not cols:
            return []
        return [x.strip() for x in cols.split(",")]

    def get_single_custodian_data(
        self, firm: str, client: str, custdn_feed: str, dte: str
    ) -> pd.DataFrame:
        custodian_str, feed_str, region_str = self.get_custodian_n_feed(custdn_feed)
        try:
            metrics = self.get_all_recon_metrics(custodian_str)
        except KeyError:
            msg = f"{custodian_str} metrics are not configured in the custodian metric configuration file!"
            raise CustodianMetricException(msg)

        try:
            cls = getattr(dp, custodian_str)
            custodian = cls(firm, client, custodian_str, feed_str, region_str, metrics)
            df = custodian.get_custdn_data(dte)
            df["custodian_mapper"] = custodian_str
            self.recon_metric_map[custodian_str] = metrics
        except AttributeError:
            msg = f"{custodian_str} class either does not exist or is not setup correctly for {feed_str}!"
            raise CustodianFeedException(msg)
        return df

    def get_firm_custodian_data(
        self,
        firm: str,
        client: str,
        custdn_feeds: list,
        dte: str,
    ) -> pd.DataFrame:
        result = []
        for custdn_feed in custdn_feeds:
            logger.info(f"Retrieving {custdn_feed} feed for {firm}...")
            try:
                df = self.get_single_custodian_data(firm, client, custdn_feed, dte)
                result.append(df)
            except Exception as err:
                msg = f"Exception while retrieving feed from {custdn_feed} for {firm}: {err} "
                logger.error(msg)
                logger.warning("Continuing...")
        if not result:
            msg = f"Could not retrieve {firm} data feeds for: {custdn_feeds}! Please check Cloudwatch for details."
            self.custodian_data_error_msg += msg + "\n"
            raise ClientDataNotFoundException(msg)
        return pd.concat(result)

    @staticmethod
    def __column_rename(rename: str) -> Tuple:
        old_col, new_col = rename.split("|")
        return old_col.strip(), new_col.strip()

    def get_column_name_overwrites(self, cno_dict_string: str) -> dict:
        if not cno_dict_string:
            return dict()
        try:
            column_rename: List[Tuple] = [
                self.__column_rename(rename) for rename in cno_dict_string.split(",")
            ]
            column_rename_dict = {
                old_col: new_col for [old_col, new_col] in column_rename
            }
            return column_rename_dict
        except ValueError:
            msg = "Column Name Overwrite is invalid. Correct format is: old_col1|new_col1,old_col2|new_col2,..."
            raise InputValidationException(msg)

    @staticmethod
    def get_final_output_column_drops(drop_string: str) -> List[str]:
        if not drop_string:
            return list()
        try:
            column_drops = list(x.strip() for x in drop_string.split(","))
            return column_drops
        except ValueError:
            msg = "Column Drops are invalid. Correct format is: col1,col2,col3,..."
            raise InputValidationException(msg)

    @staticmethod
    def get_firm_specific_post_recon_logic(firm: str, client: str, df: pd.DataFrame):
        res = df
        try:
            cls = getattr(dc, firm.title())
            client_instance = cls(firm, client)
            res = client_instance.apply_recon_post_processing_logic(df)
            return res
        except AttributeError:
            msg = f"No post-processing logic found for {firm}."
            logger.info(msg)
            return res
        except Exception as e:
            msg = f"Could not apply post processing logic to {firm} data due to error: {e}"
            raise FirmSpecificLogicException(msg)

    @staticmethod
    def get_alive_positions_in_recon(df: pd.DataFrame):
        no_d1g1t_qty = df.filter(like="d1g1t_units").isnull().all(axis=1)
        no_custodian_qty = df.filter(like="custodian_units").isnull().all(axis=1)
        dead_idx = no_d1g1t_qty & no_custodian_qty & df["units_reconciled"]
        return df[~dead_idx]

    def run_custodian_validation(
        self,
        firm: str,
        client: str,
        client_version: str,
        dte: str,
        reporting_currency: str,
    ) -> None:
        d1g1t_input_path = self.client_info["d1g1t_input_file_path"]
        output_paths = self.client_info["output_file_destination"].split(",")
        custdn_feeds = self.client_info["custodian_feed_map"].split(",")
        slack_webhook_urls = self.client_info["slack_webhook_URL"].split(",")
        recon_funds = self.client_info["recon_funds"]
        rename_column_map = self.get_column_name_overwrites(
            self.client_info["column_name_overwrite"]
        )
        column_drops = self.get_final_output_column_drops(
            self.client_info["final_output_column_drops"]
        )
        ignored_accounts = get_ignored_accounts(
            self.client_info["ignore_accounts_file"]
        )
        threshold_settings = self.get_threshold_settings(
            self.client_info["threshold_settings"]
        )
        additional_output_columns = self.get_additional_columns(
            self.client_info["additional_output_columns"]
        )
        custodian_df = self.get_firm_custodian_data(firm, client, custdn_feeds, dte)
        d1g1t_df = get_d1g1t_client_data(
            firm,
            client,
            d1g1t_input_path,
            self.environment,
            client_version,
            recon_funds,
            dte,
            reporting_currency,
            self.custodian_aliases,
        )
        recon_frame = validate_custodian_data(
            custodian_df,
            d1g1t_df,
            threshold_settings,
            self.recon_metric_map,
            ignored_accounts,
            additional_output_columns,
        )
        recon_frame = self.get_alive_positions_in_recon(recon_frame)
        recon_frame = self.get_firm_specific_post_recon_logic(firm, client, recon_frame)

        # archive old files from previous day
        for source_path in output_paths:
            try:
                archive_s3_files(source_path, archive_name="archive")
            except Exception as e:
                msg = f"Could not archive {source_path} due to the following exception: {e}"
                logger.error(msg)
                continue

        output_filenames = []
        output_filenames_excs = []

        # generate breaking accounts and store output report file names
        for output_path in reversed(output_paths):
            output_filename = get_recon_output_filename(
                self.environment, output_path, client, dte, ""
            ).strip()
            output_filename_excs = get_recon_output_filename(
                self.environment, output_path, client, dte, "_exceptions"
            ).strip()

            generate_breaking_accounts(
                recon_frame,
                self.environment,
                d1g1t_input_path,
                output_path,
                client,
                dte,
            )

            output_filenames.append(output_filename)
            output_filenames_excs.append(output_filename_excs)

        # send summary to spotlight
        try:
            send_recon_to_spotlight(
                recon_frame=recon_frame,
                client_info=self.client_info,
                environment=self.environment,
                client_version=client_version,
                dte=dte,
            )
        except Exception as e:
            msg = f"Could not send recon summaries to spotlight: {e}"
            logger.error(msg)

        # slack summary reporting
        for slack_channel in slack_webhook_urls:
            try:
                send_recon_summary(
                    recon_frame=recon_frame,
                    client=client,
                    dte=dte,
                    output_filename=output_filenames[0],
                    client_info=self.client_info,
                    slack_webhook_URL=slack_channel.strip(),
                )
            except ValueError:
                msg = "slack channel is not provided for posting summary."
                logger.error(msg)
                logger.warning("Continuing...")

        recon_frame_excs = recon_frame[
            recon_frame.filter(like="_reconciled").eq(False).any(axis=1)
        ]

        # drop and rename columns
        try:
            for frame in [recon_frame, recon_frame_excs]:
                frame.drop(column_drops, axis=1, inplace=True)
                frame.rename(columns=rename_column_map, inplace=True)
        except KeyError:
            msg = "At least one column in drop or renaming list could not be found in recon output."
            logger.error(msg)
            logger.warning("Continuing...")

        # generate output files
        for output_filename, output_filename_excs in zip(
            output_filenames, output_filenames_excs
        ):
            generate_output_file(recon_frame, d1g1t_input_path, output_filename, client)
            generate_output_file(
                recon_frame_excs, d1g1t_input_path, output_filename_excs, client
            )
        return output_filename


def run(
    firm: str,
    client: str,
    date: str,
    environment: str,
    client_version: str,
    client_info: dict,
    custodian_metric_map: dict,
    reporting_currency: str,
    custodian_aliases: dict,
):
    runner = CustodianValidation(
        environment, client_info, custodian_metric_map, custodian_aliases
    )
    output_filename = runner.run_custodian_validation(
        firm=firm,
        client=client,
        client_version=client_version,
        dte=date,
        reporting_currency=reporting_currency,
    )
    return output_filename
