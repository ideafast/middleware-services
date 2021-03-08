import csv
import json
import re
from datetime import datetime
from enum import Enum
from functools import lru_cache
from math import floor
from pathlib import Path
from typing import Any, List, Union


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
def read_csv_from_cache(path: Path) -> List[dict]:
    """
    Load full CSV into memory for quick lookup
    """
    with open(path) as csv_file:
        data = [row for row in csv.DictReader(csv_file)]
    return data


def read_json(filepath: Path) -> Any:
    with open(filepath, "r") as f:
        data = f.read()
    return json.loads(data)


def write_json(filepath: Path, data: dict) -> None:
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)


def wear_time_in_ms(weartime: str) -> int:
    """Converts DMP formatted weartime (20210101) to miliseconds."""
    return int(datetime.strptime(weartime, "%Y%m%d").timestamp() * 1e3)


def normalise_day(_datetime: datetime) -> datetime:
    """
    Replaces day time with zero for comparison by day.
    """
    return _datetime.replace(hour=0, minute=0, second=0)


def validate_and_format_patient_id(ideafast_id: str) -> Union[bool, str]:
    """
    Validate a (messy) IDEAFAST id, based on ideafast/ideafast-idgen
    Returns boolean if validate with corrected formatting
    """

    if type(ideafast_id) is str:
        id_without_punc = re.sub(r"[^\w]", "", ideafast_id)
        #  TODO: remove spaces if present

        if len(id_without_punc) == 7:
            study_site = id_without_punc[0]
            idgen = id_without_punc[1:]
            remainder = __get_remainder(idgen, 1)
            return f"{study_site}{idgen}" if remainder == 0 else False

    return False


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
