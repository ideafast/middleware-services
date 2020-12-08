from pydantic import BaseModel
from typing import Optional


class PatientDevice(BaseModel):
    patient_id: str
    device_id: str
    checkout: str
    checkin : Optional[str]