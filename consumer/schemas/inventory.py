from typing import Optional

from pydantic import BaseModel


class HistoryItem(BaseModel):
    patient_id: str
    datetime: str

    @classmethod
    def serialize(cls, device: dict) -> "HistoryItem":
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
