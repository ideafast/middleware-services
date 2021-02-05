from data_transfer.services import ucam
from data_transfer.utils import format_weartime


def test_get_record_success(mock_data: None) -> None:
    result = ucam.get_record("K-ABC123")

    assert result.patient.id == "K-ABC123"
    assert len(result.devices) == 3


def test_get_record_none(mock_data: None) -> None:
    result = ucam.get_record("NO_PATIENT_ID")

    assert result is None


def test_get_vtt_sma_hash(mock_data: None) -> None:
    record = ucam.get_record("K-DEF456")
    records = [r for r in record.devices if r.id == "NULL"]

    result = records[0].vttsma_id

    assert result == "HASH_ID"


def test_device_history_exists(mock_data: None) -> None:
    result = ucam.device_history("AX6-123456")

    assert len(result) == 2


def test_device_history_empty(mock_data: None) -> None:
    result = ucam.device_history("NO_DEVICE_ID")

    assert result == []


def test_device_wear_period(mock_data: None) -> None:
    device_id = "AX6-123456"
    start_wear = format_weartime("10/07/2020", "ucam")
    end_wear = format_weartime("14/07/2020", "ucam")

    result = ucam.record_by_wear_period(device_id, start_wear, end_wear)

    assert result.device_id == device_id
