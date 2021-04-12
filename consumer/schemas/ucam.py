from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


class DiseaseType(Enum):
    Healthy = 1  #
    HD = 2  # Huntington's
    IBD = 3  # Inflammatory bowel
    PD = 4  # Parkinson's
    PSS = 5  # Progressive systemic sclerosis
    RA = 6  # Rheumatoid arthritis
    SLE = 7  # Systemic lupus erythematosus


@dataclass
class DeviceBase:
    # GET /devices will never return None for device_id
    # GET /patients includes VTT, thus device_id _can_ be None
    device_id: Optional[str]


@dataclass
class PatientBase:
    patient_id: str
    disease: DiseaseType


@dataclass
class CommonBase:
    start_wear: datetime
    end_wear: Optional[datetime]
    deviations: Optional[str]
    vttsma_id: Optional[str]


@dataclass
class DevicePatient(PatientBase, CommonBase):
    # NOTE: is identical to VTT payload
    pass


@dataclass
class PatientDevice(DeviceBase, CommonBase):
    pass


@dataclass
class Device(DeviceBase):
    patients: List[DevicePatient]


@dataclass
class Patient(PatientBase):
    devices: List[PatientDevice]
