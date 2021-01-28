from data_transfer.config import config
from data_transfer.utils import format_weartime, read_csv_from_cache
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class UCAMPayload:
    """
    UCAM uses different field naming than our middleware. This Payload
    Creates consistency between how Records are used

    Current return values:
        SubjectID, Deviations, DeviceID, 
        VTTGeneratedParticipantID, StartDate, 
        EndDate, SubjectGroup
    """
    patient_id: str
    disease: str

    device_id: str
    devitations: str
    sma_id: str
    start_wear: datetime
    end_wear: datetime


@dataclass
class Device:
    id: str
    sma_id: str
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
    devices: [Device]


def __get_patients() -> [UCAMPayload]:
    """
    All records from the UCAM.
    
    GET /patients/
    """
    def __create_record(data: dict) -> UCAMPayload:
        """
        Convenient method to serialise payload
        """
        return UCAMPayload(
            device_id=data['DeviceID'],
            patient_id=data['SubjectID'],
            devitations=data['Deviations'],
            sma_id=data['VTTGeneratedParticipantID'],
            start_wear=format_weartime(data['StartDate'], 'ucam'),
            end_wear=format_weartime(data['EndDate'], 'ucam'),
            disease=data['SubjectGroup']
        )

    return [__create_record(d) for d in read_csv_from_cache(config.ucam_data)]


def record_by_patient_id(patient_id: str) -> PatientRecord:
    """
    Transforms the payload for consistent access with Record

    GET /patients/<patient_id>/
    """
    patient_records = [r for r in __get_patients() if r.patient_id == patient_id]
    patient = patient_records[0]
    patient = Patient(patient.patient_id, patient.disease)

    def __device_from_record(device: UCAMPayload) -> Device:
        """
        Convenient method to only store Device-specific metadata.
        """
        return Device(
            id=device.device_id, 
            sma_id=device.sma_id, 
            devitations=device.devitations,
            start_wear=device.start_wear,
            end_wear=device.end_wear
        )

    devices = [__device_from_record(r) for r in patient_records]
    return PatientRecord(patient, devices)


def device_history(device_id: str) -> [UCAMPayload]:
    return [r for r in __get_patients() if r.device_id == device_id]


def record_id_by_data_creation(device_id: str, start_wear: datetime, end_wear: datetime) -> UCAMPayload:
    """
    If data was created on a certain period then it belongs to an individual patient.
    """
    device_wear_periods = device_history(device_id)

    for record in device_wear_periods:
        within_start_period = start_wear >= record.start_wear <= record.end_wear
        within_end_period = record.start_wear <= end_wear <= record.end_wear

        if within_start_period and within_end_period:
            return record
    


# specific information about device
patient_record = record_by_patient_id('K-ZH4ZYY')
print(patient_record)

# i.e., all patients that used a specific device
# we can then use wear period to determine use ...
history = device_history('DRM-DAX2S4')
print (history)

# i.e., if a device is used by multiple patients and
# we know when data was created we can determine patient ID
record_found = record_id_by_data_creation('DRM-DAX2S4', format_weartime('29/10/2020', 'ucam'), format_weartime('31/10/2020', 'ucam'))
print (record_found.patient_id)