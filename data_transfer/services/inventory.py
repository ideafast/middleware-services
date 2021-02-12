from datetime import datetime
from typing import Any, Optional

import requests

from data_transfer import utils
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


def patient_id_by_device_id(
    device_id: str, start_wear: datetime, end_wear: datetime
) -> Optional[Any]:
    device_wears = [i for i in device_history(device_id).values()]

    def up_t(d: datetime) -> datetime:
        return d.replace(hour=0, minute=0, second=0)

    for record in device_wears:
        inventory_start_wear = utils.format_weartime(record["checkout"], "inventory")
        checkin = record["checkin"] or datetime.now().strftime(
            utils.FORMATS["inventory"]
        )
        inventory_end_wear = utils.format_weartime(checkin, "inventory")
        # While we could compare to the second, this caused some issues, e.g.,
        # when a record was created on the day for testing but not checked out until afterwards.
        start_wear = up_t(start_wear)
        inventory_start_wear = up_t(inventory_start_wear)
        inventory_end_wear = up_t(inventory_end_wear)
        end_wear = up_t(end_wear)

        within_start_period = inventory_start_wear <= start_wear <= inventory_end_wear
        within_end_period = inventory_start_wear <= end_wear <= inventory_end_wear

        if within_start_period and within_end_period:
            return record
    return None
