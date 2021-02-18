from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class Payload:
    """
    UCAM uses different field naming than our middleware. This Payload
    Creates consistency between how Records are used

    Current return values from UCAM DB:
        SubjectID, Deviations, DeviceID,
        VTTGeneratedParticipantID, StartDate,
        EndDate, SubjectGroup
    """

    patient_id: str
    disease: str

    device_id: str
    devitations: str
    vttsma_id: str
    start_wear: datetime
    end_wear: datetime


@dataclass
class Device:
    device_id: str
    vttsma_id: str
    devitations: str
    start_wear: datetime
    end_wear: datetime


@dataclass
class Patient:
    id: str
    disease: str


@dataclass
class PatientRecord:
    """
    Simplifies accessing Devices a Patient used.
    """

    patient: Patient
    devices: List[Device]
