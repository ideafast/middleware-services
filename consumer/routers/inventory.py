# See: https://snipe-it.readme.io/reference
from typing import Dict, List, Optional

from fastapi import APIRouter

from consumer.schemas.device import Device
from consumer.schemas.patient import PatientDevice
from consumer.services import inventory
from consumer.utils.errors import CustomException

router = APIRouter()


def serialize_device(device: dict) -> Device:
    """Simplifies reuse across inventory API."""

    def name_or_none(item: dict) -> Optional[str]:
        return item.get("name", None) if item else None

    return Device(
        device_id=device["asset_tag"],
        model=name_or_none(device["model"]),
        manufacturer=name_or_none(device["manufacturer"]),
        is_checkout=device["status_label"]["status_meta"] == "deployed",
        location=name_or_none(device["location"]),
        serial=device["serial"].replace(" ", ""),
        id=device["id"],
    )


@router.get("/devices/bytype/{model_id}")
async def devices_by_type(model_id: int) -> List[Device]:
    """Retrieve metadata about ALL devices for by a specific model."""
    url = f"hardware?limit=500&model_id={model_id}"
    res = await inventory.response(url)
    return [serialize_device(i) for i in res["rows"]]


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
    return serialize_device(sorted_rows[0]) if len(sorted_rows) > 0 else None


@router.get("/device/byid/{device_id}")
async def device_by_id(device_id: str) -> Device:
    """Similar to byserial but does lookup by Device ID"""
    url = f"hardware/bytag/{device_id}"
    device = await inventory.response(url)

    if device.get("status", "") == "error":
        raise CustomException(errors=[device["messages"]], status_code=404)

    return serialize_device(device)


@router.get("/device/history/{device_id}")
async def device_history(device_id: str) -> Dict[str, PatientDevice]:
    """
    The history of a device based on its ID within the inventory.
    This is NOT the serial ID nor the tag ID.
    """
    # ID required for activity endpoint is only returned by serial endpoint.
    device = await device_by_id(device_id)
    params = {"item_id": device.id, "item_type": "asset"}
    res = await inventory.response("reports/activity", params)

    history: Dict[str, PatientDevice] = dict()

    pairs = [
        (device_use["target"]["name"].strip(), device_use["created_at"]["datetime"])
        for device_use in res["rows"]
        if device_use["target"]
    ]

    for patient_id, __ in pairs:
        if patient_id not in history:
            # Response contains
            datetimes = sorted([r[1] for r in pairs if r[0] == patient_id])

            # The device will always have a checkout from the response,
            # but may not have a checkin, e.g., if device with a patient.
            checkout = datetimes[0]
            #  In that case, checkin is None
            checkin = datetimes[-1] if len(datetimes) > 1 else None

            history[patient_id] = PatientDevice(
                patient_id=patient_id,
                device_id=device_id,
                checkout=checkout,
                checkin=checkin,
            )

    return history
