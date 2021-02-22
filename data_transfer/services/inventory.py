import time
from datetime import datetime
from functools import lru_cache
from typing import Any, Optional

import requests

from data_transfer import utils
from data_transfer.config import config


def device_id_by_serial(serial: str) -> str:
    # TODO: there is a rate limit on the inventory!
    response = requests.get(f"{config.inventory_api}device/byserial/{serial}")
    # TODO: validation
    return response.json()["data"]["device_id"]


def device_history(device_id: str) -> Any:
    response = requests.get(f"{config.inventory_api}device/history/{device_id}")
    # TODO: validation
    return response.json()["data"]


@lru_cache
def record_by_device_id(
    device_id: str, start_wear: datetime, end_wear: datetime
) -> Optional[Any]:
    """
    Retreive history of a given device_id, and compute whether this particular
    time period was present in that history. If true, return that patient_id.
    NOTE: Cached method to reduce api calls when downloading multiple files for
    a single data recording
    """
    device_wears = [i for i in device_history(device_id).values()]

    # TODO: inventory has small rate limit.
    time.sleep(4)

    start_wear = utils.normalise_day(start_wear)
    end_wear = utils.normalise_day(end_wear)

    for record in device_wears:
        inventory_start_wear = utils.format_weartime(record["checkout"], "inventory")
        checkin = record["checkin"] or datetime.now().strftime(
            utils.FORMATS["inventory"]
        )
        inventory_end_wear = utils.format_weartime(checkin, "inventory")

        inventory_start_wear = utils.normalise_day(inventory_start_wear)
        inventory_end_wear = utils.normalise_day(inventory_end_wear)

        within_start_period = inventory_start_wear <= start_wear <= inventory_end_wear
        within_end_period = inventory_start_wear <= end_wear <= inventory_end_wear

        if within_start_period and within_end_period:
            return record
    return None
