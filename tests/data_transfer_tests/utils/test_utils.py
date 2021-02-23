import pytest

from data_transfer.utils import (
    __format_id_ideafast,
    __get_remainder,
    format_id_device,
    format_id_patient,
)


def test_patient_valid() -> None:
    result = format_id_patient("KNXYP6F")

    assert result == "KNXYP6F"


def test_device_valid() -> None:
    result = format_id_device("ABC-FYCRXH")

    assert result == "ABC-FYCRXH"


def test_device_ideafast_valid_no_prefix() -> None:
    result = __format_id_ideafast("FYCRXH", 0)

    assert result == "FYCRXH"


def test_device_ideafast_valid() -> None:
    result = __format_id_ideafast("ABC-FYCRXH", 4)

    assert result == "ABC-FYCRXH"


def test_device_ideafast_invalid() -> None:
    result = __format_id_ideafast("FYCRXW", 1)

    assert result is False


def test_invalid() -> None:
    result = format_id_patient("K-NXYP6G")

    assert result is False


def test_punctuation() -> None:
    result = format_id_patient("K-NXYP6F.")

    assert result == "KNXYP6F"


def test_tabs_spaces() -> None:
    result = format_id_patient("K-N XYP6\tF ")

    assert result == "KNXYP6F"


def test_length_patient() -> None:
    result = format_id_patient("K-NXYP6FF")

    assert result is False


def test_length_device() -> None:
    result = format_id_device("K-NXYP6FF")

    assert result is False


@pytest.mark.parametrize(
    "key, expected",
    [("HT", 9), ("4NT4K", 14), ("QRJA4DRS7", 23), ("FGEET9TY7Z6S5ZG", 10)],
)
def test_derived_remainders(key: str, expected: int) -> None:
    result = (__get_remainder(key, 2), __get_remainder(key, 1))

    assert result[0] == expected
    assert result[1] == 0
