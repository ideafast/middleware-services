from data_transfer.services import ucam
from data_transfer.utils import format_weartime

from datetime import datetime

import pytest


def test_get_record_success(mock_data):
    # Act
    record = ucam.get_record("K-ABC123")
    # Assert
    assert record.patient.id == "K-ABC123"
    assert len(record.devices) == 3


def test_get_record_none(mock_data):
    record = ucam.get_record("NO_PATIENT_ID")
    assert record == None


def test_get_vtt_sma_hash(mock_data):
    record = ucam.get_record("K-DEF456")
    records = [r for r in record.devices if r.id == "NULL"]
    assert records[0].vttsma_id == "HASH_ID"


def test_device_history_exists(mock_data):
    records = ucam.device_history("AX6-123456")
    # This specific device was worn by two patients
    assert len(records) == 2


def test_device_history_empty(mock_data):
    records = ucam.device_history("NO_DEVICE_ID")
    assert records == []


def test_device_wear_period(mock_data):
    device_id = "AX6-123456"
    start_wear = format_weartime("10/07/2020", "ucam")
    end_wear = format_weartime("14/07/2020", "ucam")

    record = ucam.record_by_wear_period(device_id, start_wear, end_wear)
    assert record.device_id == device_id
