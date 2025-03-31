import json
import logging
import requests
from typing import Optional

import boto3
import pandas as pd
from tabulate import tabulate
from datetime import datetime
import time
from layers.recon.datehandler import DateUtils, STD_DATE_FORMAT, HM_DATE_FORMAT
from pytz import timezone

et = timezone("US/Eastern")
SPOTLIGHTPSMETRICSPERFORMANCE = (
    "https://spotlight.d1g1tapps.com/api/v1/metrics/performance/"
)
SPOTLIGHTRECONBASE = "https://spotlight.d1g1tapps.com/api/v1/recon/"

logger = logging.getLogger(__name__)


def generate_summary_rows(
    recon_frame: pd.DataFrame,
    client_info: dict,
) -> list:
    results = []
    reporting_frame = recon_frame[
        recon_frame["Note"].astype(str) != "Account ignored during reconciliation"
    ]
    all_custodians = reporting_frame["custodian"].unique().tolist()
    reconciled_cols = reporting_frame.filter(regex="_reconciled$").columns.tolist()
    all_metrics = list(
        map(lambda col_name: col_name.split("_reconciled")[0], reconciled_cols)
    )
    slack_report_metrics_overwrite = client_info["slack_report_metrics_overwrite"]
    if slack_report_metrics_overwrite:
        all_metrics = slack_report_metrics_overwrite.split(",")
    slack_report_exceptions_only = client_info["slack_report_exceptions_only"]
    for custdn_feed in all_custodians:
        for metric in all_metrics:
            try:
                recon_custodin = reporting_frame[
                    reporting_frame["custodian"] == custdn_feed
                ]
            except Exception:
                recon_custodin = reporting_frame
            breaks = recon_custodin[
                recon_custodin[f"{metric}_reconciled"].isin([False])
            ]
            row = [
                custdn_feed,
                metric,
                len(breaks),
                "{:.2%}".format(
                    1 - round(len(breaks) / max(1, len(recon_custodin)), 4)
                ),
                len(recon_custodin),
            ]
            if slack_report_exceptions_only and len(breaks) == 0:
                continue
            else:
                results.extend([row])
    if len(results) > 25:
        results = []
    if len(all_custodians) > 1:
        for metric in all_metrics:
            breaks = reporting_frame[
                reporting_frame[f"{metric}_reconciled"].isin([False])
            ]
            row = [
                "Total",
                metric,
                len(breaks),
                "{:.2%}".format(1 - round(len(breaks) / len(reporting_frame), 4)),
                len(reporting_frame),
            ]
            if slack_report_exceptions_only and len(breaks) == 0:
                continue
            else:
                results.extend([row])

    return results


def generate_custodian_recon_summary(
    recon_frame: pd.DataFrame,
    client: str,
    dte: str,
    output_filename: str,
    client_info: dict,
) -> str:
    results = generate_summary_rows(recon_frame, client_info)

    trimmed_results = [row[:-1] for row in results]

    # Use the tabulate function to create the table
    response = tabulate(
        trimmed_results,
        headers=["Metric", "Break Count", "Percentage"],
        tablefmt="grid",
    )
    text = f"""Recon summary as of {dte} for {client},
        ```{response}```\n For more information please refer to {output_filename}.
        """
    return text


def get_outlier_summary(
    df: pd.DataFrame, client: str, dte: str, output_filename: str, outlier_type: str
) -> str:
    results = []
    breaks = df[
        df[f"{outlier_type}_outlier"].isin([True])
    ]  # TODO: update with correct fields
    row = [
        f"{outlier_type}",
        len(breaks),
        "{:.2%}".format(round(len(breaks) / len(df), 4)),
    ]
    results.extend([row])
    # Use the tabulate function to create the table
    response = tabulate(
        results, headers=["Metric", "Outlier Count", "Percentage"], tablefmt="grid"
    )
    text = f"""{outlier_type} outlier summary as of {dte} for {client},
        ```{response}```\n For more information please refer to {output_filename}.
        """
    return text


def send_slack_msg(message: str, slack_webhook_URL: str) -> None:
    payload = '{"text": "%s"}' % message
    try:
        requests.post(slack_webhook_URL, data=payload)
    except Exception:
        msg = "No slack channel provided for posting report"
        logger.error(msg)
        logger.warning("Continuing...")


def post_recon_summary_spotlight(data, headers):
    """Attempt to post the summary data."""
    successes = []
    failures = []

    for payload in data:
        response = requests.post(
            f"{SPOTLIGHTRECONBASE}summaries/", json=payload, headers=headers
        )
        if response.status_code == 201:
            print("Successfully created a firm recon summary:", response.json())
            successes.append(payload)
        elif response.status_code == 400:
            print("Failed to create firm recon summary:", response.json())
            failures.append((payload, response.json()))
        else:
            print("Unexpected response:", response.status_code)
            failures.append((payload, {"error": "Unexpected response"}))

    return successes, failures


def send_recon_to_spotlight(
    recon_frame: pd.DataFrame,
    client_info: dict,
    environment: str,
    client_version: str,
    dte: str,
) -> None:
    """Sends the recon summary to Spotlight API endpoints."""
    send_spotlight = environment.lower() == "production"

    if send_spotlight:
        try:
            custodian_feed_map = client_info.get("custodian_feed_map", "")
            if custodian_feed_map:
                entries = custodian_feed_map.split(", ")
                regions = [entry.split("|")[-1] for entry in entries]
                unique_regions = set(regions)
                if len(unique_regions) != 1:
                    raise ValueError(
                        f"Regions are not consistent in custodian_feed_map: {regions}"
                    )

                region = unique_regions.pop()
                if region == "ca":
                    region_str = "ca-central-1"
                elif region == "us":
                    region_str = "us-east-1"
                else:
                    raise ValueError(f"Unexpected region value: {region}")
            else:
                raise ValueError("No custodian_feed_map provided in client_info.")

            results = generate_summary_rows(recon_frame, client_info)

            client = boto3.client("secretsmanager", region_name=region_str)
            secret_value = client.get_secret_value(SecretId="d1g1t/spotlight")
            secret = json.loads(secret_value["SecretString"])
            token = secret["recon-headless"]

            logger.debug("[SpotlightMessenger] Token received")

            payloads = []
            for result in results:
                percent = float(result[3].strip("%")) / 100
                payload = {
                    "firm": client_info.get("name"),
                    "custodian": result[0].lower().replace(" ", "_"),
                    "metric": result[1].lower(),
                    "recon_date": dte,
                    "total_position_count": int(result[4]),
                    "break_count": result[2],
                    "environment": environment,
                    "script_version": client_version,
                    "extra": {"break_percentage": percent},
                }
                payloads.append(payload)

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            successes, failures = post_recon_summary_spotlight(payloads, headers)

            for failed_payload, error_details in failures:
                missing_slugs = {
                    key: failed_payload.get(key)
                    for key in ["firm", "custodian", "metric"]
                    if key in error_details
                }
                if missing_slugs:
                    start_time = time.time()
                    post_performance_metric(
                        missing_slugs=missing_slugs,
                        payload=failed_payload,
                        headers=headers,
                        environment=environment,
                        region=region,
                        client_version=client_version,
                        start_time=start_time,
                    )

            if not failures:
                logger.error("[SpotlightMessenger] All payloads posted successfully.")
            else:
                logger.error(
                    f"[SpotlightMessenger] {len(failures)} payload(s) failed and performance metrics were logged."
                )
        except client.exceptions.ResourceNotFoundException:
            logger.exception("[SpotlightMessenger] Requested secret was not found")
        except client.exceptions.InvalidRequestException as e:
            logger.exception(f"[SpotlightMessenger] Invalid request {e}")
        except client.exceptions.InvalidParameterException as e:
            logger.exception(f"[SpotlightMessenger] Invalid Parameters {e}")
        except Exception as e:
            logger.exception(f"[SpotlightMessenger] An error occurred {e}")


def post_performance_metric(
    missing_slugs: dict,
    payload: dict,
    headers: dict,
    environment: str,
    region: str,
    client_version: str,
    start_time: float,
):
    """Post a PerformanceMetric to indicate missing slugs and their values."""

    performance_data = {
        "firm": payload.get("firm"),
        "firm_name": payload.get("firm"),
        "environment": environment,
        "region": region,
        "ps_version": client_version,
        "ps_revision": "NA",
        "label": "recon_summary_status",
        "tags": [
            {"slug": slug, "value": value} for slug, value in missing_slugs.items()
        ],
        "status": "Incomplete",
        "duration": round((time.time() - start_time), 1),
        "extra": {
            "Reason": "Missing slugs during recon summary post",
            "Details": missing_slugs,
        },
    }
    response = requests.post(
        SPOTLIGHTPSMETRICSPERFORMANCE, json=performance_data, headers=headers
    )
    if response.status_code == 201:
        logger.info("Successfully posted a PerformanceMetric:", response.json())
        return True
    else:
        logger.info(
            "Failed to post PerformanceMetric. Response:",
            response.status_code,
            response.text,
        )
        return False


def send_recon_summary(
    recon_frame: pd.DataFrame,
    client: str,
    dte: str,
    output_filename: str,
    client_info: dict,
    slack_webhook_URL: Optional[str] = None,
    recon_type: str = "custodian",
) -> None:
    if dte == DateUtils.get_last_cob_date():
        dte = dte.strftime("%Y-%m-%d")
    if recon_type == "custodian":
        recon_summary = generate_custodian_recon_summary(
            recon_frame, client, dte, output_filename, client_info
        )
    else:
        recon_summary = get_outlier_summary(
            recon_frame, client, dte, output_filename, outlier_type=recon_type
        )

    send_slack_msg(recon_summary, slack_webhook_URL)


def generate_output_file(
    recon_frame: pd.DataFrame,
    d1g1t_input_path: str,
    output_filename: str,
    client: str,
):
    logger.info(f"Saving validation file for {client} as {output_filename}....")
    sep = "|" if client == "assante" else ","
    try:
        recon_frame.to_csv(
            output_filename,
            index=False,
            sep=sep,
            storage_options={
                "s3_additional_kwargs": {
                    "ACL": "bucket-owner-full-control",
                    "Metadata": {
                        "creator": "refresh_recon",
                        "source": json.dumps([d1g1t_input_path]),
                        "empty": "true" if recon_frame.empty else "false",
                    },
                },
            },
        )
        s3 = boto3.client("s3")
        *_, bucket, key = output_filename.split("/", 3)
        s3_tag = {"TagSet": [{"Key": "client", "Value": client}]}
        s3.put_object_tagging(Bucket=bucket, Key=key, Tagging=s3_tag)
    except Exception:
        msg = f"Failed to generate file {output_filename}...."
        logger.error(msg)
        logger.warning("Continuing...")


def get_recon_output_filename(
    environment: str,
    output_path: str,
    client: str,
    dte: str,
    file_extenison: Optional[str],
    recon_type: str = "custodian",
):
    timestamp = datetime.now(et).strftime(HM_DATE_FORMAT)
    if recon_type == "custodian":
        return f"{output_path}/{client}_validation_{environment}_{dte}-{timestamp}{file_extenison}.csv"
    else:
        return f"{output_path}/{client}_{recon_type}_outlier_report_{environment}_{dte}-{timestamp}{file_extenison}.csv"


def generate_breaking_accounts(
    recon_frame: pd.DataFrame,
    environment: str,
    d1g1t_input_path: str,
    output_path: str,
    client: str,
    dte: str,
):
    if dte == DateUtils.get_last_cob_date():
        dte = dte.strftime(STD_DATE_FORMAT)
        file_name = f"{output_path}/{client}_breaking_accounts_{environment}_{dte}.csv"
    else:
        file_name = f"{output_path}/{client}_breaking_accounts_{environment}_{dte}.csv"

    recon_col = "units_reconciled"
    if recon_col in recon_frame.columns:
        unique_accounts = pd.DataFrame(
            recon_frame[recon_frame[recon_col].eq(False)]["account"].unique(),
            columns=["account"],
        )
        if not unique_accounts.empty:
            generate_output_file(unique_accounts, d1g1t_input_path, file_name, client)
