from typing import Optional

from pydantic import BaseModel


class PatientDevice(BaseModel):
    patient_id: str
    device_id: str
    checkout: str
    checkin: Optional[str]
