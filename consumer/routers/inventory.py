# See: https://snipe-it.readme.io/reference
from fastapi import APIRouter

from consumer.schemas.device import Device
from consumer.schemas.patient import PatientDevice
from consumer.services import inventory
from consumer.utils.errors import CustomException

router = APIRouter()


def serialize_device(device: dict) -> Device:
    """Simplifies reuse across inventory API."""

    def name_or_none(item: dict):
        return item.get("name", None) if item else None

    return Device(
        device_id=device["asset_tag"],
        model=name_or_none(device["model"]),
        manufacturer=name_or_none(device["manufacturer"]),
        is_checkout=device["status_label"]["status_meta"] == "deployed",
        location=name_or_none(device["location"]),
        serial=device["serial"],
        id=device["id"],
    )


@router.get("/device/byserial/{serial}")
async def device_by_serial(serial: str) -> Device:
    """Retrieve metadata about a device based on its serial code."""
    url = f"hardware/byserial/{serial}"
    res = await inventory.response(url)
    rows = res["rows"]

    if len(rows) == 0:
        raise CustomException(errors=["No device with that code."], status_code=404)

    # Note: multiple devices may exist with same serial,
    # e.g. DRMDAX2S4 and DRM-DAX2S4. As such, sort by use.
    rows = sorted(rows, key=lambda k: k["checkout_counter"], reverse=True)
    return serialize_device(rows[0]) if len(rows) > 0 else []


@router.get("/device/byid/{device_id}")
async def device_by_id(device_id: str) -> Device:
    """Similar to byserial but does lookup by Device ID"""
    url = f"hardware/bytag/{device_id}"
    device = await inventory.response(url)

    if device.get("status", "") == "error":
        raise CustomException(errors=[device["messages"]], status_code=404)

    return serialize_device(device)


@router.get("/device/history/{device_id}")
async def device_history(device_id: str) -> [PatientDevice]:
    """
    The history of a device based on its ID within the inventory.
    This is NOT the serial ID nor the tag ID.
    """
    # ID required for activity endpoint is only returned by serial endpoint.
    device = await device_by_id(device_id)
    params = {"item_id": device.id, "item_type": "asset"}
    res = await inventory.response("reports/activity", params)

    history = {}

    # The device has been assigned to a patient ID.
    rows = [row for row in res["rows"] if row["target"]]

    for row in rows:
        item = PatientDevice(
            patient_id=row["target"]["name"].strip(),
            device_id=device_id,
            checkout=row["created_at"]["datetime"],
        )
        # Device has been returned
        if item.patient_id in history:
            # Sorting by checkout implies last item is checkin date.
            # Each history activity uses the same date for checkin/out.
            pairs = sorted([item.checkout, history[item.patient_id].checkout])
            item.checkout, item.checkin = pairs
        history[item.patient_id] = item
    return history
