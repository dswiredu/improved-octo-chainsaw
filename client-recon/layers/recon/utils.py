import logging
from typing import Optional
import json
import pandas as pd
import boto3
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


def get_json(json_str: str = None, path: str = None) -> dict:
    """
    Read json from a file path or convert json string to json object.

    :param: json_str: string or json obj
    :param: file: full path to .json file
    """
    if not path and not json_str:
        raise TypeError("At least one of path/json string inputs must be provided!")
    if json_str:
        return json.loads(json_str)
    else:
        with open(path, "r", encoding="utf-8") as infile:
            return json.load(infile)


def get_ignored_accounts(file: Optional[str] = None) -> set:
    """Gets set of accounts to be ignored accross all recons."""
    ignored_accounts = set()
    try:
        df = pd.read_csv(file, dtype=str, usecols=["AccountID"])
        ignored_accounts = set(df["AccountID"])
    except FileNotFoundError:
        msg = f"No ignore accounts file found at {file}!"
        logger.error(msg)
    except KeyError:
        msg = "Expected 'AccountID' column in ignore accounts file. Could not find it!"
        logger.error(msg)
    except ValueError:
        msg = "No ignore accounts file provided!"
        logger.error(msg)
        logger.warning("Continuing...")
    return ignored_accounts


def read_url(s3_url):
    parsed_url = urlparse(s3_url)
    if parsed_url.scheme == "s3" and parsed_url.netloc and parsed_url.path:
        bucket_name = parsed_url.netloc
        key = parsed_url.path.lstrip("/")
        return bucket_name, key


def get_file_by_prefix(date: str, bucket_name: str, prefix: str) -> str:
    s3 = boto3.client("s3")
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        if "Contents" in page:
            for obj in page["Contents"]:
                if date in obj["Key"]:
                    file_name = obj["Key"]
                    return file_name


def archive_s3_files(source_url, archive_name):
    """Read url and restore files from S3 if needed then archive all"""
    s3 = boto3.client("s3")
    source_bucket, source_prefix = read_url(source_url)

    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=source_bucket, Prefix=source_prefix):
        for content in page["Contents"]:
            file_key = content["Key"]
            if file_key.endswith(".csv"):
                if archive_name in file_key:
                    continue

                parts = file_key.split("/")
                parts.insert(-1, archive_name)
                destination_key = "/".join(parts)

                # check the storage class
                page_metadata = s3.head_object(Bucket=source_bucket, Key=file_key)
                storage_class = page_metadata.get("StorageClass", "STANDARD")

                if storage_class in ["GLACIER", "DEEP_ARCHIVE"]:
                    s3.restore_object(
                        Bucket=source_bucket,
                        Key=file_key,
                        RestoreRequest={
                            "Days": 1,
                            "GlacierJobParameters": {"Tier": "Standard"},
                        },
                    )

                copy_source = {"Bucket": source_bucket, "Key": file_key}
                try:
                    s3.copy_object(
                        Bucket=source_bucket,
                        Key=destination_key,
                        CopySource=copy_source,
                    )
                    logger.info(
                        f"Copied {file_key} from {source_bucket}/{source_prefix} to {source_bucket}/{destination_key}"
                    )
                    s3.delete_object(Bucket=source_bucket, Key=file_key)
                    logger.info(
                        f"Successfully deleted {file_key} from {source_bucket}."
                    )
                except Exception as e:
                    logger.info(f"Failed to copy {file_key} due to {e}")
