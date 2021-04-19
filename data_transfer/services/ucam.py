from datetime import datetime
from functools import lru_cache
from typing import List, Optional

import requests

from data_transfer.config import config
from data_transfer.schemas.ucam import (
    Device,
    DeviceWithPatients,
    Patient,
    PatientWithDevices,
)
from data_transfer.utils import normalise_day


@lru_cache
def get_one_patient(patient_id: str) -> Optional[PatientWithDevices]:
    response = requests.get(f"{config.ucam_api}patients/{patient_id}").json()
    return (
        PatientWithDevices.serialize(response["data"])
        if response["meta"]["success"]
        else None
    )


@lru_cache
def get_one_device(device_id: str) -> Optional[List[DeviceWithPatients]]:
    response = requests.get(f"{config.ucam_api}devices/{device_id}").json()
    return (
        [DeviceWithPatients.serialize(device) for device in response["data"]]
        if response["meta"]["success"]
        else None
    )


def get_all_vtt() -> Optional[List[Patient]]:
    response = requests.get(f"{config.ucam_api}vtt/").json()
    return (
        [Patient.serialize(vtt) for vtt in response["data"]]
        if response["meta"]["success"]
        else None
    )


def get_one_vtt(vtt_id: str) -> Optional[List[Patient]]:
    response = requests.get(f"{config.ucam_api}vtt/{vtt_id}").json()
    return (
        [Patient.serialize(vtt) for vtt in response["data"]]
        if response["meta"]["success"]
        else None
    )


def patient_by_wear_period(
    device_id: str, start_wear: datetime, end_wear: datetime
) -> Optional[Patient]:
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
    devices: List[Device], start_wear: datetime, end_wear: datetime
) -> Optional[Device]:
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
