from datetime import datetime
from functools import lru_cache
from typing import List, Optional

import requests

from data_transfer.config import config
from data_transfer.schemas.ucam import (
    Device,
    DevicePatient,
    DiseaseType,
    Patient,
    PatientDevice,
)
from data_transfer.utils import format_weartime, normalise_day


@lru_cache
def get_one_patient(patient_id: str) -> Optional[Patient]:
    response = requests.get(f"{config.ucam_api}patients/{patient_id}").json()
    return __as_patient(response["data"]) if response["meta"]["success"] else None


@lru_cache
def get_one_device(device_id: str) -> Optional[List[Device]]:
    response = requests.get(f"{config.ucam_api}devices/{device_id}").json()
    return (
        [__as_device(device) for device in response["data"]]
        if response["meta"]["success"]
        else None
    )


def get_all_vtt() -> Optional[List[DevicePatient]]:
    response = requests.get(f"{config.ucam_api}vtt/").json()
    return (
        [__as_devicepatient(vtt) for vtt in response["data"]]
        if response["meta"]["success"]
        else None
    )


def get_one_vtt(vtt_id: str) -> Optional[List[DevicePatient]]:
    response = requests.get(f"{config.ucam_api}vtt/{vtt_id}").json()
    return (
        [__as_devicepatient(vtt) for vtt in response["data"]]
        if response["meta"]["success"]
        else None
    )


def __as_patient(p: dict) -> Patient:
    return Patient(
        patient_id=p["patient_id"],
        disease=DiseaseType(int(p["disease"])),
        devices=[__as_patientdevice(pd) for pd in p["devices"]],
    )


def __as_patientdevice(pd: dict) -> PatientDevice:
    return PatientDevice(
        start_wear=format_weartime(pd["start_wear"], "ucam"),
        end_wear=format_weartime(pd["end_wear"], "ucam") if pd["end_wear"] else None,
        deviations=pd["deviations"],
        vttsma_id=pd["vttsma_id"],
        device_id=pd["device_id"],
    )


def __as_device(d: dict) -> Patient:
    return Device(
        device_id=d["device_id"],
        patients=[__as_devicepatient(dp) for dp in d["patients"]],
    )


def __as_devicepatient(dp: dict) -> DevicePatient:
    return DevicePatient(
        start_wear=format_weartime(dp["start_wear"], "ucam"),
        end_wear=format_weartime(dp["end_wear"], "ucam") if dp["end_wear"] else None,
        deviations=dp["deviations"],
        vttsma_id=dp["vttsma_id"],
        patient_id=dp["patient_id"],
        disease=DiseaseType(int(dp["disease"])),
    )


def patient_by_wear_period(
    device_id: str, start_wear: datetime, end_wear: datetime
) -> Optional[DevicePatient]:
    """
    If data was created on a certain period then it belongs to an individual patient.
    NOTE: returns DevicePatient, not Patient
    """
    start_wear = normalise_day(start_wear)
    end_wear = normalise_day(end_wear)
    devices = get_one_device(device_id)

    if devices:
        for device in devices:
            for patient in device.patients:

                # NOTE: ignores any device ID if record contains deviations
                # TODO: removes this constraint once faulty device_id assignment has been resolved
                if patient.deviations:
                    continue

                patient_start = normalise_day(patient.start_wear)
                # if end_wear is none, use today
                patient_end = normalise_day(patient.end_wear or datetime.today())

                within_start_period = patient_start <= start_wear <= patient_end
                within_end_period = patient_start <= end_wear <= patient_end

                if within_start_period and within_end_period:
                    return patient
    return None


def device_by_wear_period(
    devices: List[PatientDevice], start_wear: datetime, end_wear: datetime
) -> Optional[PatientDevice]:
    """
    If data was created on a certain period then it belongs to an individual patient.
    NOTE: returns PatientDevice, not Device
    """
    start_wear = normalise_day(start_wear)
    end_wear = normalise_day(end_wear)

    for device in devices:
        device_start_wear = normalise_day(device.start_wear)
        # if end_wear is none, use today
        device_end_wear = normalise_day(device.end_wear or datetime.today())

        within_start_period = device_start_wear <= start_wear <= device_end_wear
        within_end_period = device_start_wear <= end_wear <= device_end_wear

        if within_start_period and within_end_period:
            return device
    return None
