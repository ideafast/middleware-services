import os
from datetime import datetime
from typing import List, Optional

import requests

from consumer.schemas.ucam import (
    Device,
    DevicePatient,
    DiseaseType,
    Patient,
    PatientDevice,
)


def __ucam_access_token() -> str:
    """Obtain (or refresh) an access token."""
    now = int(datetime.utcnow().timestamp())
    last_created = int(os.getenv("UCAM_ACCESS_TOKEN_GEN_TIME", 0))
    # Refresh the token every 1 day, i.e., below 7 day limit.
    token_expired = (last_created + (60 * 60 * 24)) <= now

    if token_expired:
        request = {
            "Username": os.getenv("UCAM_USERNAME"),
            "Password": os.getenv("UCAM_PASSWORD"),
        }

        response = requests.post(f"{os.getenv('UCAM_URI')}/user/login", json=request)
        response.raise_for_status()
        result: dict = response.json()
        access_token = result["token"]

        os.environ["UCAM_ACCESS_TOKEN"] = access_token
        os.environ["UCAM_ACCESS_TOKEN_GEN_TIME"] = str(now)

    return os.getenv("UCAM_ACCESS_TOKEN")


def response(request_url: str) -> Optional[dict]:
    """
    Performs GET request on the UCAM API
    NOTE: requests automatically converts null to None
    """
    headers = {"Authorization": f"Bearer {__ucam_access_token()}"}
    url = f"{os.getenv('UCAM_URI')}{request_url}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    # possibly no result
    if response.status_code == 204:
        return None

    result: dict = response.json()
    return result


def get_patients() -> Optional[List[Patient]]:
    # NOTE: patients/patient_id returns a 204 if not found, other endpoints []
    payload = response("/patients/")
    return [as_patient(patient) for patient in payload] if payload else None


def get_one_patient(patient_id: str) -> Optional[Patient]:
    # NOTE: patients/patient_id returns a 204 if not found, other endpoints []
    payload = response(f"/patients/{patient_id}")
    return as_patient(payload) if payload else None


def get_devices(device_id: str = "") -> Optional[List[Device]]:
    # always returns a list, even for one device_id
    payload = response(f"/devices/{device_id}")
    return [as_device(device) for device in payload] if payload else None


def get_vtt(vtt_id: str = "") -> Optional[List[DevicePatient]]:
    # always returns a list, even for one vvt_id; also cannot be assumed to be unique
    payload = response(f"/devices/VTT/{vtt_id}")
    return [as_devicepatient(vtt) for vtt in payload] if payload else None


def as_patient(p: dict) -> Patient:
    return Patient(
        patient_id=p["subject_id"],
        disease=DiseaseType(int(p["subject_Group"])),
        devices=[as_patientdevice(pd) for pd in p["devices"]],
    )


def as_patientdevice(pd: dict) -> PatientDevice:
    return PatientDevice(
        start_wear=__format_weartime(pd["start_Date"]),
        end_wear=__format_weartime(pd["end_Date"]) if pd["end_Date"] else None,
        deviations=pd["deviations"],
        vttsma_id=pd["vtT_id"],
        device_id=pd["device_id"],
    )


def as_device(d: dict) -> Device:
    return Device(
        device_id=d["device_id"],
        patients=[as_devicepatient(dp) for dp in d["patients"]],
    )


def as_devicepatient(dp: dict) -> DevicePatient:
    return DevicePatient(
        start_wear=__format_weartime(dp["start_Date"]),
        end_wear=__format_weartime(dp["end_Date"]) if dp["end_Date"] else None,
        deviations=dp["deviations"],
        vttsma_id=dp["vtT_id"],
        patient_id=dp["subject_id"],
        disease=DiseaseType(int(dp["subject_Group"])),
    )


def __format_weartime(time: str) -> datetime:
    """create a datetime object from a UCAM provide weartime string"""
    return datetime.strptime(time, "%Y-%m-%dT%H:%M:%S")
