from pydantic import BaseModel
from typing import Optional


class Device(BaseModel):
    id: int
    serial: str
    device_id: str
    is_checkout: bool
    model: Optional[str]
    manufacturer: Optional[str]
    location: Optional[str]