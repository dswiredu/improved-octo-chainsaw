import json


def load_json(path) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def save_json(obj, path) -> None:
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
