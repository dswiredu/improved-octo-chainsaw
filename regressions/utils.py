"""internal app script utilities."""

import json
from typing import Optional

import boto3
from botocore.exceptions import ClientError


def get_json(json_str: Optional[str] = None, path: Optional[str] = None) -> dict:
    """
    Read json from a file path or convert json string to json object.

    :param: json_str: string or json obj
    :param: file: full path to .json file
    """
    if not path and not json_str:
        raise TypeError("At least one of path/json string inputs must be provided!")
    if json_str:
        return json.loads(json_str)
    if path.startswith("s3"):
        s3_resource = boto3.resource("s3")
        *_, bucket, key = path.split("/", 3)
        try:
            s3obj = s3_resource.Object(bucket, key)
            s3_file = s3obj.get()["Body"].read()
            return json.loads(s3_file)
        except ClientError as err:
            if err.response["Error"]["Code"] == "NoSuchKey":
                # file does not exist
                return {}
            raise
    else:
        with open(path, "r", encoding="utf-8") as infile:
            return json.load(infile)


def save_json(path: str, json_obj: dict) -> None:
    """Save json object."""
    if path.startswith("s3"):
        s3_resource = boto3.resource("s3")
        *_, bucket, key = path.split("/", 3)
        s3obj = s3_resource.Object(bucket, key)
        s3obj.put(Body=json.dumps(json_obj, indent=4), ACL="bucket-owner-full-control")
    else:
        with open(path, "w", encoding="utf-8") as outfile:
            json.dump(json_obj, outfile)
