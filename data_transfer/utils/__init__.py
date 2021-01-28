from datetime import datetime
from pathlib import Path
import json


def format_inventory_weartime(period: str):
    datetime_format = "%Y-%m-%d %H:%M:%S"
    # NOTE: as the device may not been returned yet (i.e. still in use)
    # we set the end_wear as today. TODO: temporary until UCAM db access.
    if not period: 
        return datetime.now().strftime(datetime_format)
    return datetime.strptime(period, datetime_format)


def read_json(filepath: Path) -> json:
    with open(filepath, 'r') as f:
            data = f.read()
    return json.loads(data)


def write_json(filepath: Path, data: dict) -> None:
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)