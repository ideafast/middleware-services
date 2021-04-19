from __future__ import annotations

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
class Patient(PatientBase, CommonBase):
    # NOTE: is identical to VTT payload

    @classmethod
    def serialize(cls, payload: dict) -> Patient:
        return cls(
            start_wear=format_weartime(payload["start_Date"]),
            end_wear=format_weartime(payload["end_Date"])
            if payload["end_Date"]
            else None,
            deviations=payload["deviations"],
            vttsma_id=payload["vtT_id"],
            patient_id=payload["subject_id"],
            disease=DiseaseType(int(payload["subject_Group"])),
        )


@dataclass
class Device(DeviceBase, CommonBase):
    @classmethod
    def serialize(cls, payload: dict) -> Device:
        return cls(
            start_wear=format_weartime(payload["start_Date"]),
            end_wear=format_weartime(payload["end_Date"])
            if payload["end_Date"]
            else None,
            deviations=payload["deviations"],
            vttsma_id=payload["vtT_id"],
            device_id=payload["device_id"],
        )


@dataclass
class DeviceWithPatients(DeviceBase):
    patients: List[Patient]

    @classmethod
    def serialize(cls, payload: dict) -> DeviceWithPatients:
        return cls(
            device_id=payload["device_id"],
            patients=[Patient.serialize(patients) for patients in payload["patients"]],
        )


@dataclass
class PatientWithDevices(PatientBase):
    devices: List[Device]

    @classmethod
    def serialize(cls, payload: dict) -> PatientWithDevices:
        return cls(
            patient_id=payload["subject_id"],
            disease=DiseaseType(int(payload["subject_Group"])),
            devices=[Device.serialize(devices) for devices in payload["devices"]],
        )


def format_weartime(time: str) -> datetime:
    """create a datetime object from a UCAM provide weartime string"""
    return datetime.strptime(time, "%Y-%m-%dT%H:%M:%S")
