from datetime import datetime
from functools import lru_cache
from typing import Any, Optional

import requests

from data_transfer import utils
from data_transfer.config import config


@lru_cache
def all_devices_by_type(device_type: utils.DeviceType) -> Any:
    """
    Retrieve complete list of ALL Devices by model.
    This is cached as response can be quite large and will be used multiple times per DAG."""
    model_id = dict(BTF=6, DRM=8)[device_type.name]
    response = requests.get(f"{config.inventory_api}devices/bytype/{model_id}")
    return response.json()


def device_id_by_serial(device_type: utils.DeviceType, serial: str) -> Optional[str]:
    response = all_devices_by_type(device_type)
    return next(
        (i["device_id"] for i in response["data"] if i["serial"] == serial), None
    )


@lru_cache
def device_history(device_id: str) -> Any:
    response = requests.get(f"{config.inventory_api}device/history/{device_id}")
    # TODO: validation
    _response = response.json()
    if not _response["meta"]["success"]:
        return None
    return _response["data"]


@lru_cache
def record_by_device_id(
    device_id: str, start_wear: datetime, end_wear: datetime
) -> Optional[Any]:
    history = device_history(device_id)
    if not history:
        return None

    start_wear = utils.normalise_day(start_wear)
    end_wear = utils.normalise_day(end_wear)

    for record in history.values():
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
