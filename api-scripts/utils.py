import json
from typing import Optional


def get_json(
    json_str: Optional[str] = None, path: Optional[str] = None
) -> dict:
    """
    :param: json_str: string or json obj
    :param: file: full path to .json file
    """
    if not path and not json_str:
        raise TypeError(
            "At least one of path/json string inputs must be provided!"
        )
    if json_str:
        return json.loads(json_str)
    elif path:
        with open(path, "r") as f:
            return json.load(f)


def save_json(path: str, json_obj: dict) -> None:
        with open(path, "w") as outfile:
            json.dump(json_obj, outfile)


