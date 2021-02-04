from enum import Enum
from datetime import datetime
from pathlib import Path
from functools import lru_cache

import csv
import json


class DeviceType(Enum):
    AX6 = 1  # Axivity
    BTF = 2  # Byteflies
    DRM = 3  # Dreem
    TFA = 4  # Think Fast
    BVN = 5  # Everion
    MMM = 6  # Move Monitor
    SMP = 7  # Samsung Smartphone
    SMA = 8  # Stress Monitor App
    BED = 9  # EBedSensor
    VTP = 10  # Vital Patch
    YSM = 11  # ZKOne YOLI


FORMATS = {"ucam": "%d/%m/%Y", "inventory": "%Y-%m-%d %H:%M:%S"}


def format_weartime(period: str, type: str) -> datetime:
    return datetime.strptime(period, FORMATS[type])


@lru_cache(maxsize=None)
def read_csv_from_cache(path: Path) -> [dict]:
    """
    Load full CSV into memory for quick lookup
    """
    with open(path) as csv_file:
        data = [row for row in csv.DictReader(csv_file)]
    return data


def read_json(filepath: Path) -> json:
    with open(filepath, "r") as f:
        data = f.read()
    return json.loads(data)


def write_json(filepath: Path, data: dict) -> None:
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)
