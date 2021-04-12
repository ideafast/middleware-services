from unittest.mock import MagicMock, patch

from data_transfer.schemas.ucam import Device, DevicePatient, Patient
from data_transfer.services import ucam
from data_transfer.utils import format_weartime


def test_get_patient_success(mock_data: dict, mock_payload: dict) -> None:
    mock_payload["data"] = mock_data["patients"][0]
    get_response = MagicMock(json=lambda: mock_payload)

    with patch("requests.get", return_value=get_response):

        result = ucam.get_one_patient("E-PATIENT")

        assert isinstance(result, Patient)
        assert result.patient_id == "E-PATIENT"
        assert len(result.devices) == 1
        assert result.disease == ucam.DiseaseType.PD


def test_get_patient_not_found() -> None:
    mock_payload = {
        "data": None,
        "meta": {"success": False, "errors": ["No patient with that id."]},
    }
    get_response = MagicMock(json=lambda: mock_payload)

    with patch("requests.get", return_value=get_response):

        result = ucam.get_one_patient("X-PATIENT")

        assert result is None


def test_get_device_success(mock_data: dict, mock_payload: dict) -> None:
    mock_payload["data"] = [
        d for d in mock_data["devices"] if d["device_id"] == "NR3-DEVICE"
    ]
    get_response = MagicMock(json=lambda: mock_payload)

    with patch("requests.get", return_value=get_response):

        result = ucam.get_one_device("NR3-DEVICE")

        assert all(isinstance(x, Device) for x in result)
        assert len(result) == 1
        assert result[0].device_id == "NR3-DEVICE"
        assert all(isinstance(x, DevicePatient) for x in result[0].patients)


def test_get_device_not_found() -> None:
    mock_payload = {
        "data": None,
        "meta": {"success": False, "errors": ["No device with that id."]},
    }
    get_response = MagicMock(json=lambda: mock_payload)

    with patch("requests.get", return_value=get_response):

        result = ucam.get_one_device("NOT-DEVICE")

        assert result is None


def test_get_vtt_success(mock_data: dict, mock_payload: dict) -> None:
    mock_payload["data"] = mock_data["vtt"]
    get_response = MagicMock(json=lambda: mock_payload)

    with patch("requests.get", return_value=get_response):

        result = ucam.get_one_vtt("VTT_COMPLEX_HASH")

        assert len(result) == 2
        assert result[0].vttsma_id == "VTT_COMPLEX_HASH"
        assert result[1].vttsma_id == "VTT_COMPLEX_HASH"
        assert all(isinstance(x, DevicePatient) for x in result)


def test_get_vtts_success(mock_data: dict, mock_payload: dict) -> None:
    mock_payload["data"] = mock_data["vtt"]
    get_response = MagicMock(json=lambda: mock_payload)

    with patch("requests.get", return_value=get_response):

        result = ucam.get_all_vtt()

        assert len(result) == 2
        assert all(isinstance(x, DevicePatient) for x in result)


def test_get_patient_by_period_date_within(mock_data: dict, mock_payload: dict) -> None:
    mock_payload["data"] = [
        d for d in mock_data["devices"] if d["device_id"] == "NR3-DEVICE"
    ]
    get_response = MagicMock(json=lambda: mock_payload)

    device_id = "NR3-DEVICE"
    start_wear = format_weartime("2020-06-20T00:00:00", "ucam")
    end_wear = format_weartime("2020-06-20T00:00:01", "ucam")

    with patch("requests.get", return_value=get_response):

        result = ucam.patient_by_wear_period(device_id, start_wear, end_wear)

        assert result.patient_id == "B-PATIENT"


def test_get_patient_by_period_invalid_patient_id(mock_payload: dict) -> None:
    get_response = MagicMock(json=lambda: mock_payload)

    device_id = "WRONG-DEVICE-ID"
    start_wear = format_weartime("2020-06-20T00:00:00", "ucam")
    end_wear = format_weartime("2020-06-20T00:00:01", "ucam")

    with patch("requests.get", return_value=get_response):

        result = ucam.patient_by_wear_period(device_id, start_wear, end_wear)

        assert result is None


def test_get_patient_by_period_date_with_endwear_none(
    mock_data: dict, mock_payload: dict
) -> None:
    mock_payload["data"] = [
        d for d in mock_data["devices"] if d["device_id"] == "NR3-DEVICE"
    ]
    get_response = MagicMock(json=lambda: mock_payload)

    device_id = "NR3-DEVICE"
    start_wear = format_weartime("2020-07-25T00:00:00", "ucam")
    end_wear = format_weartime("2020-07-26T00:00:00", "ucam")

    with patch("requests.get", return_value=get_response):

        result = ucam.patient_by_wear_period(device_id, start_wear, end_wear)

        assert result.patient_id == "B-PATIENT"


def test_get_patient_by_period_date_not_found(
    mock_data: dict, mock_payload: dict
) -> None:
    mock_payload["data"] = [
        d for d in mock_data["devices"] if d["device_id"] == "NR3-DEVICE"
    ]
    get_response = MagicMock(json=lambda: mock_payload)

    device_id = "NR3-DEVICE"
    start_wear = format_weartime("2020-06-01T00:00:00", "ucam")
    end_wear = format_weartime("2020-06-01T00:00:00", "ucam")

    with patch("requests.get", return_value=get_response):

        result = ucam.patient_by_wear_period(device_id, start_wear, end_wear)

        assert result is None


def test_get_device_by_period_date_within(mock_data: dict) -> None:
    patient = ucam.__as_patient(mock_data["patients"][5])
    start_wear = format_weartime("2020-09-09T00:00:00", "ucam")
    end_wear = format_weartime("2020-09-09T00:00:01", "ucam")

    result = ucam.device_by_wear_period(patient.devices, start_wear, end_wear)

    assert result.device_id == "NR5-DEVICE"


def test_get_device_by_period_date_within_vtt(mock_data: dict) -> None:
    patient = ucam.__as_patient(mock_data["patients"][5])
    start_wear = format_weartime("2020-09-22T00:00:00", "ucam")
    end_wear = format_weartime("2020-09-22T00:00:01", "ucam")

    result = ucam.device_by_wear_period(patient.devices, start_wear, end_wear)

    assert result.device_id is None
    assert result.vttsma_id == "VTT_COMPLEX_HASH"


def test_get_device_by_period_date_outside(mock_data: dict) -> None:
    patient = ucam.__as_patient(mock_data["patients"][5])
    start_wear = format_weartime("2020-09-10T00:00:00", "ucam")
    end_wear = format_weartime("2020-09-13T00:00:01", "ucam")

    result = ucam.device_by_wear_period(patient.devices, start_wear, end_wear)

    assert result is None


def test_get_device_by_period_date_end_wear_none(mock_data: dict) -> None:
    patient = ucam.__as_patient(mock_data["patients"][5])
    start_wear = format_weartime("2020-09-29T00:00:00", "ucam")
    end_wear = format_weartime("2020-10-02T00:00:01", "ucam")

    result = ucam.device_by_wear_period(patient.devices, start_wear, end_wear)

    assert result.vttsma_id == "VTT_COMPLEX_HASH"
