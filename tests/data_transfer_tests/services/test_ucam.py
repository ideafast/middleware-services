from unittest.mock import MagicMock, patch

from data_transfer.schemas.ucam import DiseaseType, PatientWithDevices
from data_transfer.services import ucam
from data_transfer.utils import format_weartime


def test_get_patient_success(
    mock_ucam_config: MagicMock, mock_data: dict, mock_payload: dict
) -> None:
    mock_payload.update({"data": mock_data["patients"][0]})
    get_response = MagicMock(json=lambda: mock_payload)

    with patch("requests.get", return_value=get_response):

        result = ucam.get_one_patient("E-PATIENT")

        assert result.patient_id == "E-PATIENT"
        assert len(result.devices) == 1

        # test if casting to DiseaseType went OK
        assert result.disease == DiseaseType.PD


def test_get_patient_not_found(mock_ucam_config: MagicMock, mock_payload: dict) -> None:
    mock_payload.update(
        {
            "data": None,
            "meta": {"success": False, "errors": ["No patient with that id."]},
        }
    )
    get_response = MagicMock(json=lambda: mock_payload)

    with patch("requests.get", return_value=get_response):

        result = ucam.get_one_patient("X-PATIENT")

        assert result is None


def test_get_device_success(
    mock_ucam_config: MagicMock, mock_data: dict, mock_payload: dict
) -> None:
    mock_payload.update(
        {"data": [d for d in mock_data["devices"] if d["device_id"] == "NR3-DEVICE"]}
    )
    get_response = MagicMock(json=lambda: mock_payload)

    with patch("requests.get", return_value=get_response):

        result = ucam.get_one_device("NR3-DEVICE")

        assert len(result) == 1
        assert result[0].device_id == "NR3-DEVICE"


def test_get_device_not_found(mock_ucam_config: MagicMock, mock_payload: dict) -> None:
    mock_payload.update(
        {
            "data": None,
            "meta": {"success": False, "errors": ["No device with that id."]},
        }
    )
    get_response = MagicMock(json=lambda: mock_payload)

    with patch("requests.get", return_value=get_response):

        result = ucam.get_one_device("NOT-DEVICE")

        assert result is None


def test_get_vtt_success(
    mock_ucam_config: MagicMock, mock_data: dict, mock_payload: dict
) -> None:
    mock_payload.update({"data": mock_data["vtt"]})
    get_response = MagicMock(json=lambda: mock_payload)

    with patch("requests.get", return_value=get_response):

        result = ucam.get_one_vtt("VTT_COMPLEX_HASH")

        assert len(result) == 2
        assert result[0].vttsma_id == result[1].vttsma_id == "VTT_COMPLEX_HASH"


def test_get_vtts_success(
    mock_ucam_config: MagicMock, mock_data: dict, mock_payload: dict
) -> None:
    mock_payload.update({"data": mock_data["vtt"]})
    get_response = MagicMock(json=lambda: mock_payload)

    with patch("requests.get", return_value=get_response):

        result = ucam.get_all_vtt()

        assert len(result) == 2


def test_get_patient_by_period_date_within(mock_data: dict, mock_payload: dict) -> None:
    mock_payload.update(
        {"data": [d for d in mock_data["devices"] if d["device_id"] == "NR3-DEVICE"]}
    )
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
    mock_data: dict, mock_payload: dict, mock_ucam_config: MagicMock
) -> None:
    mock_payload.update(
        {"data": [d for d in mock_data["devices"] if d["device_id"] == "NR3-DEVICE"]}
    )
    get_response = MagicMock(json=lambda: mock_payload)

    device_id = "NR3-DEVICE"
    start_wear = format_weartime("2020-07-25T00:00:00", "ucam")
    end_wear = format_weartime("2020-07-26T00:00:00", "ucam")

    with patch("requests.get", return_value=get_response):

        result = ucam.patient_by_wear_period(device_id, start_wear, end_wear)

        assert result.patient_id == "B-PATIENT"


def test_get_patient_by_period_date_not_found(
    mock_data: dict, mock_payload: dict, mock_ucam_config: MagicMock
) -> None:
    mock_payload.update(
        {"data": [d for d in mock_data["devices"] if d["device_id"] == "NR3-DEVICE"]}
    )
    get_response = MagicMock(json=lambda: mock_payload)

    device_id = "NR3-DEVICE"
    start_wear = format_weartime("2020-06-01T00:00:00", "ucam")
    end_wear = format_weartime("2020-06-01T00:00:00", "ucam")

    with patch("requests.get", return_value=get_response):

        result = ucam.patient_by_wear_period(device_id, start_wear, end_wear)

        assert result is None


# NOTE: this is a temporary measure until device_id's are corrected in
# the UCAM database and confirmed by all study sites
# See data_transfer/services/ucam/patient_by_wear_period
def test_get_patient_by_period_date_ignore_deviations(
    mock_data: dict, mock_payload: dict, mock_ucam_config: MagicMock
) -> None:
    mock_payload.update(
        {"data": [d for d in mock_data["devices"] if d["device_id"] == "NR3-DEVICE"]}
    )
    get_response = MagicMock(json=lambda: mock_payload)

    device_id = "NR3-DEVICE"
    start_wear = format_weartime("2020-07-21T00:00:00", "ucam")
    end_wear = format_weartime("2020-07-21T00:00:01", "ucam")

    with patch("requests.get", return_value=get_response):

        result = ucam.patient_by_wear_period(device_id, start_wear, end_wear)

        assert result is None


def test_get_device_by_period_date_within(
    mock_data: dict, mock_ucam_config: MagicMock
) -> None:
    patient = PatientWithDevices.serialize(mock_data["patients"][5])
    start_wear = format_weartime("2020-09-09T00:00:00", "ucam")
    end_wear = format_weartime("2020-09-09T00:00:01", "ucam")

    result = ucam.device_by_wear_period(patient.devices, start_wear, end_wear)

    assert result.device_id == "NR5-DEVICE"


def test_get_device_by_period_date_within_vtt(
    mock_data: dict, mock_ucam_config: MagicMock
) -> None:
    patient = PatientWithDevices.serialize(mock_data["patients"][5])
    start_wear = format_weartime("2020-09-22T00:00:00", "ucam")
    end_wear = format_weartime("2020-09-22T00:00:01", "ucam")

    result = ucam.device_by_wear_period(patient.devices, start_wear, end_wear)

    assert result.device_id is None
    assert result.vttsma_id == "VTT_COMPLEX_HASH"


def test_get_device_by_period_date_outside(
    mock_data: dict, mock_ucam_config: MagicMock
) -> None:
    patient = PatientWithDevices.serialize(mock_data["patients"][5])
    start_wear = format_weartime("2020-09-10T00:00:00", "ucam")
    end_wear = format_weartime("2020-09-13T00:00:01", "ucam")

    result = ucam.device_by_wear_period(patient.devices, start_wear, end_wear)

    assert result is None


def test_get_device_by_period_date_end_wear_none(
    mock_data: dict, mock_ucam_config: MagicMock
) -> None:
    patient = PatientWithDevices.serialize(mock_data["patients"][5])
    start_wear = format_weartime("2020-09-29T00:00:00", "ucam")
    end_wear = format_weartime("2020-10-02T00:00:01", "ucam")

    result = ucam.device_by_wear_period(patient.devices, start_wear, end_wear)

    assert result.vttsma_id == "VTT_COMPLEX_HASH"
