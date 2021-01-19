from datetime import datetime
from pathlib import Path
import json


def format_weartime(period: str) -> str:
    return datetime.fromtimestamp(period).strftime("%d-%m-%Y")


def read_json(filepath: Path) -> json:
    with open(filepath, 'r') as f:
            data = f.read()
    return json.loads(data)


def write_json(filepath: Path, data: dict) -> None:
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)