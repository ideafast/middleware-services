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
