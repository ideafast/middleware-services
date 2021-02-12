from datetime import datetime
from typing import List, Optional

from data_transfer.config import config
from data_transfer.schemas.ucam import Device, Patient, PatientRecord, Payload
from data_transfer.utils import format_weartime, read_csv_from_cache


def __get_patients() -> List[Payload]:
    """
    All records from the UCAM DB.

    GET /patients/
    """

    def __create_record(data: dict) -> Payload:
        """
        Convenient method to serialise payload.
        Creates mapping between UCAM and our intended use.
        """
        return Payload(
            device_id=data["DeviceID"],
            patient_id=data["SubjectID"],
            devitations=data["Deviations"],
            vttsma_id=data["VTTGeneratedParticipantID"],
            start_wear=format_weartime(data["StartDate"], "ucam"),
            end_wear=format_weartime(data["EndDate"], "ucam"),
            disease=data["SubjectGroup"],
        )

    return [__create_record(d) for d in read_csv_from_cache(config.ucam_data)]


def __serialise_records(patient_records: List[Payload]) -> Optional[PatientRecord]:
    """
    All records from the UCAM DB.

    GET /patients/
    """
    # No records exist for that patient,
    # e.g., if a device was not worn or a staff member forget to add the record
    if len(patient_records) == 0:
        return None

    # Records returned from UCAM contain the patient ID in each row.
    # Rather than duplicating this, we create it once, then associate
    # all other rows (i.e., devices) below
    patient = patient_records[0]
    patient = Patient(patient.patient_id, patient.disease)

    def __device_from_record(device: Payload) -> Device:
        """
        Convenient method to only store Device-specific metadata.
        """
        return Device(
            device_id=device.device_id,
            vttsma_id=device.vttsma_id,
            devitations=device.devitations,
            start_wear=device.start_wear,
            end_wear=device.end_wear,
        )

    devices = [__device_from_record(r) for r in patient_records]
    return PatientRecord(patient, devices)


def get_record(patient_id: str) -> Optional[PatientRecord]:
    """
    Transforms the payload for consistent access with Record

    GET /patients/<patient_id>/
    """
    patient_records = [r for r in __get_patients() if r.patient_id == patient_id]
    return __serialise_records(patient_records)


def record_by_vtt(vtt_hash: str) -> Optional[PatientRecord]:
    """
    Return a patient record based on then Hashed ID provided by VTT
    The VTT hashes are unique to each patient

    GET /vtt/<vtt_hash>/
    """
    patient_records = [r for r in __get_patients() if r.vttsma_id == vtt_hash]
    return __serialise_records(patient_records)


def device_history(device_id: str) -> List[Payload]:
    """
    A device may be worn by many patients. This returns such history.
    """
    return [r for r in __get_patients() if r.device_id == device_id]


def record_by_wear_period(
    device_id: str, start_wear: datetime, end_wear: datetime
) -> Optional[Payload]:
    """
    If data was created on a certain period then it belongs to an individual patient.
    """
    device_wear_periods = device_history(device_id)

    def up_t(d: datetime) -> datetime:
        return d.replace(hour=0, minute=0, second=0)

    for record in device_wear_periods:

        start_wear = up_t(start_wear)
        drm_start_wear = up_t(record.start_wear)
        drm_end_wear = up_t(record.end_wear)
        end_wear = up_t(end_wear)

        within_start_period = drm_start_wear <= start_wear <= drm_end_wear
        within_end_period = drm_start_wear <= end_wear <= drm_end_wear
        if within_start_period and within_end_period:
            return record
    return None


def record_by_wear_period_in_list(
    devices: List[Device], start_wear: datetime, end_wear: datetime
) -> Optional[Payload]:
    """
    If data was created on a certain period then it belongs to an individual patient.
    """
    print(len(devices), start_wear, end_wear)
    for record in devices:
        within_start_period = record.start_wear <= start_wear <= record.end_wear
        within_end_period = record.start_wear <= end_wear <= record.end_wear
        if within_start_period and within_end_period:
            return record
    return None
