from data_transfer.services import ucam
from data_transfer.utils import format_weartime

from pathlib import Path
from datetime import datetime

import pytest


def mock_data_path():
    folder = Path(__file__).parent
    return f"{folder}/data/mock_ucam_db.csv"


def test_get_record_success():
    # Arrange
    ucam.config.ucam_data = mock_data_path()
    # Act
    record = ucam.get_record('K-ABC123')
    # Assert
    assert record.patient.id == 'K-ABC123'
    assert len(record.devices) == 3


def test_get_record_none():
    ucam.config.ucam_data = mock_data_path()
    record = ucam.get_record('NO_PATIENT_ID')
    assert record == None


def test_get_vtt_sma_hash():
    ucam.config.ucam_data = mock_data_path()
    record = ucam.get_record('K-DEF456')
    records = [r for r in record.devices if r.id == 'NULL']
    assert records[0].vttsma_id == "HASH_ID"


def test_device_history_exists():
    ucam.config.ucam_data = mock_data_path()
    records = ucam.device_history('AX6-123456')
    # This specific device was worn by two patients
    assert len(records) == 2


def test_device_history_empty():
    ucam.config.ucam_data = mock_data_path()
    records = ucam.device_history('NO_DEVICE_ID')
    assert records == []


def test_device_wear_period():
    ucam.config.ucam_data = mock_data_path()
    device_id = 'AX6-123456'
    start_wear = format_weartime('10/07/2020', 'ucam')
    end_wear = format_weartime('14/07/2020', 'ucam')

    record_or_none = ucam.record_by_wear_period(device_id, start_wear, end_wear)

    assert record_or_none.device_id == device_id