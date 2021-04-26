import os
from collections import defaultdict
from datetime import datetime
from typing import List, Optional

import requests

from consumer.schemas.ucam import DeviceWithPatients, Patient, PatientWithDevices


def ucam_access_token() -> str:
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
    headers = {"Authorization": f"Bearer {ucam_access_token()}"}
    url = f"{os.getenv('UCAM_URI')}{request_url}"

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    # possibly no result
    if response.status_code == 204:
        return None

    result: dict = response.json()
    return result


def get_patients() -> Optional[List[PatientWithDevices]]:
    # NOTE: patients/patient_id returns a 204 if not found, other endpoints []
    payload = response("/patients/")
    return (
        [PatientWithDevices.serialize(patient) for patient in payload]
        if payload
        else None
    )


def get_one_patient(patient_id: str) -> Optional[PatientWithDevices]:
    # NOTE: patients/patient_id returns a 204 if not found, other endpoints []
    payload = response(f"/patients/{patient_id}")
    return PatientWithDevices.serialize(payload) if payload else None


def get_devices(device_id: str = "") -> Optional[List[DeviceWithPatients]]:
    # always returns a list, even for one device_id
    payload = response(f"/devices/{device_id}")
    return (
        [DeviceWithPatients.serialize(device) for device in payload]
        if payload
        else None
    )


def get_vtt(vtt_id: str = "") -> Optional[List[Patient]]:
    # always returns a list, even for one vvt_id; also cannot be assumed to be unique
    payload = response(f"/devices/VTT/{vtt_id}")
    return [Patient.serialize(vtt) for vtt in payload] if payload else None


dot_keys = {
    "bytefliesEEGSet1DeviceID",
    "bytefliesEEGSet2DeviceID",
    "bytefliesECGSet1DeviceID",
    "bytefliesECGSet2DeviceID",
    "bytefliesIMUSet1DeviceID",
    "bytefliesIMUSet2DeviceID",
}


def get_btfdots() -> Optional[List[DeviceWithPatients]]:
    """
    A temporary endpoint to resolve UCAM payload complexity for BTF dots
    Returns all dots transformed to devices and their associated patients
    This method can possibly be removed once UCAM refactors dots as devices
    """
    result = defaultdict(list)
    payload = response("/patients/")

    for patient in payload:
        for device in patient["devices"]:
            if device["device_id"] and device["device_id"].startswith("BTF-"):

                dots = [
                    dot
                    for key, dot in device.items()
                    if key in dot_keys and dot is not None
                ]
                for dot in dots:
                    # match raw JSON struct to be used with our serializer
                    result[dot].append(
                        {
                            "subject_id": patient["subject_id"],
                            "subject_Group": patient["subject_Group"],
                            "start_Date": device["start_Date"],
                            "end_Date": device["end_Date"],
                            "deviations": device["deviations"],
                            "vtT_id": device["vtT_id"],
                        }
                    )

    device_payload = [
        {
            "device_id": dot,
            "patients": patients,
        }
        for dot, patients in result.items()
    ]

    return (
        [DeviceWithPatients.serialize(device) for device in device_payload]
        if device_payload
        else None
    )
