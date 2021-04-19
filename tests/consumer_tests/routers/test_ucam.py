import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from consumer.schemas.ucam import DeviceWithPatients, Patient, PatientWithDevices
from consumer.services import ucam


def test_get_patient_success(mock_data: dict, client: TestClient) -> None:
    with patch.object(ucam, "response", return_value=mock_data["patients"][0]):

        result = client.get("/ucam/patients/E-PATIENT").json()

        assert result["meta"]["success"] is True
        assert len(result["data"]) > 0


def test_get_patient_not_found(mock_data: dict, client: TestClient) -> None:
    with patch.object(ucam, "response", return_value=None):

        result = client.get("/ucam/patients/NO-PATIENT").json()

        assert len(result["meta"]["errors"]) > 0
        assert result["meta"]["success"] is False
        assert result["data"] is None


def test_get_patients_success(mock_data: dict, client: TestClient) -> None:
    with patch.object(ucam, "response", return_value=mock_data["patients"]):

        result = client.get("/ucam/patients/").json()

        assert len(result["data"]) == 6
        assert result["meta"]["success"] is True


def test_get_device_success(mock_data: dict, client: TestClient) -> None:
    with patch.object(
        ucam,
        "response",
        return_value=[
            d for d in mock_data["devices"] if d["device_id"] == "NR3-DEVICE"
        ],
    ):

        result = client.get("/ucam/devices/NR3-DEVICE").json()

        assert result["meta"]["success"] is True
        assert len(result["data"]) == 1
        assert result["data"][0]["device_id"] == "NR3-DEVICE"


def test_get_device_not_found(mock_data: dict, client: TestClient) -> None:
    with patch.object(ucam, "response", return_value=None):

        result = client.get("/ucam/devices/NOT-DEVICE").json()

        assert result["meta"]["success"] is False
        assert len(result["meta"]["errors"]) > 0
        assert result["data"] is None


def test_get_devices_success(mock_data: dict, client: TestClient) -> None:
    with patch.object(ucam, "response", return_value=mock_data["devices"]):

        result = client.get("/ucam/devices/").json()

        assert len(result["data"]) == 5
        assert result["meta"]["success"] is True


def test_get_vtt_success(mock_data: dict, client: TestClient) -> None:
    with patch.object(ucam, "response", return_value=mock_data["vtt"]):

        result = client.get("/ucam/vtt/VTT_COMPLEX_HASH").json()

        assert len(result["data"]) == 2
        assert result["meta"]["success"] is True


def test_get_vtts_success(mock_data: dict, client: TestClient) -> None:
    with patch.object(ucam, "response", return_value=mock_data["vtt"]):

        result = client.get("/ucam/vtt/").json()

        assert len(result["data"]) == 2
        assert result["meta"]["success"] is True


@pytest.mark.live
def test_LIVE_auth_OK() -> None:
    with patch.dict(
        os.environ, {"UCAM_ACCESS_TOKEN": "", "UCAM_ACCESS_TOKEN_GEN_TIME": "0"}
    ):

        result = ucam.ucam_access_token()

        assert isinstance(result, str)


@pytest.mark.live
def test_LIVE_get_patients_OK() -> None:

    result = ucam.get_patients()

    assert all(isinstance(x, PatientWithDevices) for x in result)


@pytest.mark.live
def test_LIVE_get_devices_OK() -> None:

    result = ucam.get_devices()

    assert all(isinstance(x, DeviceWithPatients) for x in result)


@pytest.mark.live
def test_LIVE_get_vtt_OK() -> None:

    result = ucam.get_vtt()

    assert all(isinstance(p, Patient) for p in result)


@pytest.mark.live
def test_get_no_patients() -> None:

    result = ucam.get_one_patient("THIS PATIENT SHOULD REALLY NOT EXIST")

    assert result is None


@pytest.mark.live
def test_LIVE_get_no_devices() -> None:

    result = ucam.get_devices("THIS DEVICE SHOULD REALLY NOT EXIST")

    assert result is None


@pytest.mark.live
def test_get_no_vtt() -> None:

    result = ucam.get_vtt("THIS VTT HASH SHOULD REALLY NOT EXIST")

    assert result is None
