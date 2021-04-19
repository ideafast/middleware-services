from typing import List

from fastapi import APIRouter

from consumer.schemas.ucam import DeviceWithPatients, Patient, PatientWithDevices
from consumer.services import ucam
from consumer.utils.errors import CustomException

router = APIRouter()


@router.get("/patients")
def get_patients() -> List[PatientWithDevices]:
    """Get all patients (and their linked devices) registered in the UCAM database"""
    return ucam.get_patients()


@router.get("/patients/{patient_id}")
def get_one_patient(patient_id: str) -> PatientWithDevices:
    """Query the UCAM database for a specific patient_id"""
    res = ucam.get_one_patient(patient_id)
    if not res:
        raise CustomException(errors=["No patient with that id."], status_code=404)
    return res


@router.get("/devices")
def get_devices() -> List[DeviceWithPatients]:
    """Get all devices (and their linked patients) registered in the UCAM database"""
    return ucam.get_devices()


@router.get("/devices/{device_id}")
def get_one_device(device_id: str) -> List[DeviceWithPatients]:
    """Query the UCAM database for a specific device_id"""
    res = ucam.get_devices(device_id)
    if not res:
        raise CustomException(errors=["No device with that id."], status_code=404)
    return res


@router.get("/vtt/")
def get_vtt() -> List[Patient]:
    """Get all vtt hashes (and their linked patients) registered in the UCAM database"""
    return ucam.get_vtt()


@router.get("/vtt/{vtt_id}")
def get_one_vtt(vtt_id: str) -> List[Patient]:
    """Query the UCAM database for a specific vtt_id"""
    res = ucam.get_vtt(vtt_id)
    if not res:
        raise CustomException(errors=["No vtt with that hash_id."], status_code=404)
    return res
