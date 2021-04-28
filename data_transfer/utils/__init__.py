import csv
import hashlib
import json
import logging
import re
from datetime import datetime, timedelta
from enum import Enum
from functools import lru_cache
from math import floor
from pathlib import Path
from typing import Any, List, Optional, Tuple

log = logging.getLogger(__name__)


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


class StudySite(Enum):
    Newcastle = 1
    Kiel = 2
    Muenster = 3  # i.e. Münster
    Rotterdam = 4  # i.e. Erasmus


FORMATS = {"ucam": "%Y-%m-%dT%H:%M:%S", "inventory": "%Y-%m-%d %H:%M:%S"}


def format_weartime(period: str, type: str) -> datetime:
    """create a datetime object from a specifically formated string"""
    return datetime.strptime(period, FORMATS[type])


def format_weartime_from_timestamp(period: int) -> datetime:
    """create a datetime object from a timestamp"""
    return datetime.fromtimestamp(period)


def get_period_by_days(start: int, days: int) -> Tuple[int, int]:
    """return two timestamps based on a startdate and duration"""
    reference = datetime.today() - timedelta(days=start)

    # ensure end at night, but start in the morning to capture everything _those days_
    end_date = reference.replace(hour=23, minute=59, second=59, microsecond=999999)
    from_date = end_date - timedelta(
        days=days, hours=23, minutes=59, seconds=59, microseconds=999999
    )

    begin = int(from_date.timestamp())
    end = int(end_date.timestamp())
    return (begin, end)


def get_endwear_by_seconds(start: datetime, duration: int) -> datetime:
    """return timestamps based on a startdate and duration"""
    return start + timedelta(seconds=duration)


@lru_cache(maxsize=None)
def read_csv_from_cache(path: Path) -> List[dict]:
    """
    Load full CSV into memory for quick lookup
    NOTE: breaks if .csv not in right codec (i.e. saved from Excel)
    """
    with open(path) as csv_file:
        data = [row for row in csv.DictReader(csv_file)]
    return data


def read_json(filepath: Path) -> Any:
    with open(filepath, "r") as f:
        data = f.read()
    log.debug(f"Reading file from: {filepath}\n")
    return json.loads(data)


def write_json(filepath: Path, data: dict) -> None:
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)
    log.debug(f"JSON file saved to: {filepath}\n")


def wear_time_in_ms(weartime: str) -> int:
    """Converts DMP formatted weartime (20210101) to miliseconds."""
    return int(datetime.strptime(weartime, "%Y%m%d").timestamp() * 1e3)


def normalise_day(_datetime: datetime) -> datetime:
    """
    Replaces day time with zero for comparison by day.
    """
    return _datetime.replace(hour=0, minute=0, second=0, microsecond=0)


def format_id_patient(patient_id: str) -> Optional[str]:
    """
    Validate and formats patient id s
    NOTE: retains the '-'
    """
    return __format_id_ideafast(patient_id, 1)


def format_id_device(device_id: str) -> Optional[str]:
    """
    Validate and formats device id s
    NOTE: retains the '-'
    """
    return __format_id_ideafast(device_id, 3)


def __format_id_ideafast(ideafast_id: str, prefix_length: int) -> Optional[str]:
    """
    Validate a and formats a (messy) patient or device IDEAFAST id based on
    ideafast/ideafast-idgen. Returns boolean if validate with corrected formatting
    """
    if type(ideafast_id) is str:
        ideafast_id = ideafast_id.upper()
        # NOTE: appending a '-' in preperation of a result
        prefix = f"{ideafast_id[:prefix_length]}-"
        stripped_id = ideafast_id[prefix_length:]
        id_to_check = re.sub(r"[^\w]|_", "", stripped_id)

        if len(id_to_check) == 6:
            remainder = __get_remainder(id_to_check, 1)
            return f"{prefix}{id_to_check}" if remainder == 0 else None

    return None


def __get_remainder(string: str, factor: int) -> int:
    character_set = "ACDEFGHJKNPQRSTVXYZ2345679"
    total = 0

    # reverse iteration
    for char in string[::-1]:
        try:
            code_point = character_set.index(char)
        except (IndexError, ValueError):
            return True  # True != 0
        addend = factor * code_point
        factor = 1 if factor == 2 else 2
        addend = floor(addend / len(character_set)) + (addend % len(character_set))
        total += addend

    return total % len(character_set)


def uid_to_hash(input: str, device_type: DeviceType) -> str:
    result = hashlib.sha256()
    # deviceType is used as a salt and to improve uniqueness across
    # devices (i.e. Dreem uid != Byteflies uid)
    result.update(device_type.name.encode("utf-8"))
    result.update(input.encode("utf-8"))
    return result.hexdigest()
