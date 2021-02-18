from datetime import datetime
from typing import List, Optional

from data_transfer.config import config
from data_transfer.schemas.ucam import Device, Patient, PatientRecord, Payload
from data_transfer.utils import format_weartime, normalise_day, read_csv_from_cache


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
    records = device_history(device_id)

    return __record_in_wear_period(records, start_wear, end_wear)


def record_by_wear_period_in_list(
    devices: List[Device], start_wear: datetime, end_wear: datetime
) -> Optional[Payload]:
    """
    If data was created on a certain period then it belongs to an individual patient.
    """
    return __record_in_wear_period(devices, start_wear, end_wear)


def __record_in_wear_period(
    records: List, start_wear: datetime, end_wear: datetime
) -> Optional[Payload]:
    """
    Filters records for a specific record in a given wear period.
    """
    start_wear = normalise_day(start_wear)
    end_wear = normalise_day(end_wear)

    for record in records:
        # While we could compare records to the second, this caused some issues, e.g.,
        # when a record was created on the day for testing but not checked out until afterwards.
        record_start_wear = normalise_day(record.start_wear)
        record_end_wear = normalise_day(record.end_wear)

        within_start_period = record_start_wear <= start_wear <= record_end_wear
        within_end_period = record_start_wear <= end_wear <= record_end_wear

        if within_start_period and within_end_period:
            return record
    return None
