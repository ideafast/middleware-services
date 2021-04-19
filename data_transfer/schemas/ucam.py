from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

from data_transfer.utils import format_weartime


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
            start_wear=format_weartime(payload["start_wear"], "ucam"),
            end_wear=format_weartime(payload["end_wear"], "ucam")
            if payload["end_wear"]
            else None,
            deviations=payload["deviations"],
            vttsma_id=payload["vttsma_id"],
            patient_id=payload["patient_id"],
            disease=DiseaseType(int(payload["disease"])),
        )


@dataclass
class Device(DeviceBase, CommonBase):
    @classmethod
    def serialize(cls, payload: dict) -> Device:
        return cls(
            start_wear=format_weartime(payload["start_wear"], "ucam"),
            end_wear=format_weartime(payload["end_wear"], "ucam")
            if payload["end_wear"]
            else None,
            deviations=payload["deviations"],
            vttsma_id=payload["vttsma_id"],
            device_id=payload["device_id"],
        )


@dataclass
class DeviceWithPatients(DeviceBase):
    patients: List[Patient]

    @classmethod
    def serialize(cls, payload: dict) -> DeviceWithPatients:
        return cls(
            device_id=payload["device_id"],
            patients=[Patient.serialize(patient) for patient in payload["patients"]],
        )


@dataclass
class PatientWithDevices(PatientBase):
    devices: List[Device]

    @classmethod
    def serialize(cls, payload: dict) -> PatientWithDevices:
        return cls(
            patient_id=payload["patient_id"],
            disease=DiseaseType(int(payload["disease"])),
            devices=[Device.serialize(device) for device in payload["devices"]],
        )
