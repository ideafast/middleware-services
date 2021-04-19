from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class Device(BaseModel):
    id: int
    serial: str
    device_id: str
    is_checkout: bool
    model: Optional[str]
    manufacturer: Optional[str]
    location: Optional[str]

    @classmethod
    def serialize(cls, device: dict) -> Device:
        """Simplifies reuse across inventory API."""
        return cls(
            id=device["id"],
            serial=device["serial"].replace(" ", ""),
            device_id=device["asset_tag"],
            is_checkout=device["status_label"]["status_meta"] == "deployed",
            model=device.get("model", {}).get("name"),
            manufacturer=device.get("manufacturer", {}).get("name"),
            location=device.get("location", {}).get("name"),
        )


class HistoryItem(BaseModel):
    patient_id: str
    datetime: str

    @classmethod
    def serialize(cls, device: dict) -> HistoryItem:
        """Device is an item from a snipe-it response.
        This also contains an 'action_type' that is either 'checkout'
        or 'checkin from' but is not currently used."""
        return cls(
            patient_id=device["target"]["name"].strip(),
            datetime=device["created_at"]["datetime"],
        )


class HistoryItemResponse(BaseModel):
    patient_id: str
    device_id: str
    checkout: str
    checkin: Optional[str]
