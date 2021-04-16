# See: https://snipe-it.readme.io/reference
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter

from consumer.schemas.inventory import Device, HistoryItem, HistoryItemResponse
from consumer.services import inventory
from consumer.utils.errors import CustomException

router = APIRouter()


@router.get("/devices/bytype/{model_id}")
async def devices_by_type(model_id: int) -> List[Device]:
    """Retrieve metadata about ALL devices for by a specific model."""
    url = f"hardware?limit=500&model_id={model_id}"
    res = await inventory.response(url)
    return [Device.serialize(i) for i in res["rows"]]


@router.get("/device/byserial/{serial}")
async def device_by_serial(serial: str) -> Optional[Device]:
    """Retrieve metadata about a device based on its serial code."""
    url = f"hardware/byserial/{serial}"
    res = await inventory.response(url)
    rows = res["rows"]

    if len(rows) == 0:
        raise CustomException(errors=["No device with that code."], status_code=404)

    # Note: multiple devices may exist with same serial,
    # e.g. DRMDAX2S4 and DRM-DAX2S4. As such, sort by use.
    # TODO: typing throws as `rows` is not promised to be a `SupportsLessThan` Iterable
    sorted_rows = sorted(rows, key=lambda k: k["checkout_counter"], reverse=True)  # type: ignore
    return Device.serialize(sorted_rows[0]) if len(sorted_rows) > 0 else None


@router.get("/device/byid/{device_id}")
async def device_by_id(device_id: str) -> Device:
    """Similar to byserial but does lookup by Device ID"""
    url = f"hardware/bytag/{device_id}"
    device = await inventory.response(url)

    if device.get("status", "") == "error":
        raise CustomException(errors=[device["messages"]], status_code=404)

    return Device.serialize(device)


@router.get("/device/history/{device_id}")
async def device_history(device_id: str) -> Dict[str, HistoryItemResponse]:
    """
    The history of a device based on its ID within the inventory.
    This is NOT the serial ID nor the tag ID.
    """
    # ID required for activity endpoint is only returned by serial endpoint.
    device = await device_by_id(device_id)
    params = {"item_id": device.id, "item_type": "asset"}
    res = await inventory.response("reports/activity", params)

    # Filter response to only show relevant data for checkin/checkout (=target)
    response = [HistoryItem.serialize(row) for row in res["rows"] if row["target"]]

    history: Dict[str, HistoryItemResponse] = dict()

    for patient_id in {item.patient_id for item in response}:
        # All datetimes for checkin/checkout of a device per patient.
        # The first is the initial checkout and last (if exists) is checkin.
        datetimes = sorted(
            [r.datetime for r in response if r.patient_id == patient_id],
            key=lambda t: datetime.strptime(t, "%Y-%m-%d %H:%M:%S"),
        )

        history[patient_id] = HistoryItemResponse(
            patient_id=patient_id,
            device_id=device_id,
            # The device will always have a checkout from the response,
            checkout=datetimes[0],
            # but may not have checkin, e.g., if device is with patient.
            checkin=datetimes[-1] if len(datetimes) > 1 else None,
        )

    return history
