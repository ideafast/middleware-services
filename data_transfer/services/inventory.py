from typing import Any, Optional

import requests

from data_transfer.config import config


def device_id_by_serial(serial: str) -> str:
    # TODO: there is a rate limit on the inventory!
    response = requests.get(f"{config.inventory_api}device/byserial/{serial}")
    # TODO: validation
    return str(response.json()["data"]["device_id"])


def device_history(device_id: str) -> Any:
    response = requests.get(f"{config.inventory_api}device/history/{device_id}")
    # TODO: validation
    return response.json()["data"]


def patient_id_by_device_id(device_id: str) -> Optional[str]:
    values = [i for i in device_history(device_id).values()]

    if len(values) == 1:
        return str(values[0]["patient_id"])
    else:
        # this means that there are multiple devices in the history, e.g.
        # that multiple users may have used the same device. Therefore,
        # we also need to pass in the wear time range and filter by it.
        # TODO: check which device is within wear time range
        return None
