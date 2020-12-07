from pydantic import BaseModel


class Device(BaseModel):
    id: int
    serial: str
    device_id: str
    is_checkout: bool
    name: str
    manufacturer: str
    location: str