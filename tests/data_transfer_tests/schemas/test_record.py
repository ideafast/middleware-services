from datetime import datetime

import pytest

from data_transfer.schemas.record import Record


@pytest.fixture
def get_record() -> Record:
    return Record(
        hash="hash",
        manufacturer_ref="manufacturer_ref",
        device_type="device_type",
        device_id="device_id",
        patient_id="patient_id",
        start_wear=datetime.today(),
        end_wear=datetime.today(),
        meta=dict(
            metafield="metafield",
        ),
    )


def test_clean_record(get_record: Record) -> None:

    result = get_record

    assert result.is_downloaded is False
    assert result.is_processed is False
    assert result.is_prepared is False
    assert result.is_uploaded is False


@pytest.mark.xfail(raises=ValueError, strict=True)
def test_not_allowed_prepared(get_record: Record) -> None:
    get_record.is_downloaded = True
    # NOTE: not doing: get_record.is_processed = True

    get_record.is_prepared = True  # act


@pytest.mark.xfail(raises=ValueError, strict=True)
def test_not_allowed_uploaded(get_record: Record) -> None:
    get_record.is_downloaded = True
    get_record.is_processed = True

    get_record.is_uploaded = True  # act


@pytest.mark.xfail(raises=ValueError, strict=True)
def test_not_allowed_processed(get_record: Record) -> None:

    get_record.is_processed = True  # act


@pytest.mark.xfail(raises=ValueError, strict=True)
def test_is_set_true_after_error() -> None:
    value = True
    values = dict(is_required=False)
    required = "is_required"

    result = Record.is_set_true_after(value, values, required)

    assert result is value


def test_is_set_true_after_valid() -> None:
    value = True
    values = dict(is_required=True)
    required = "is_required"

    result = Record.is_set_true_after(value, values, required)

    assert result is value


def test_skip_validation_if_set_false() -> None:
    value = False

    result = Record.is_set_true_after(value, {}, "")

    assert result is value
