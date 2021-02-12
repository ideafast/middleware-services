import pytest

from data_transfer.utils import __get_remainder, validate_and_format_patient_id


def test_valid() -> None:
    result = validate_and_format_patient_id("KNXYP6F")

    assert result == "KNXYP6F"


def test_invalid() -> None:
    result = validate_and_format_patient_id("K-NXYP6G")

    assert result is False


def test_punctuation() -> None:
    result = validate_and_format_patient_id("K- NXYP6F .")

    assert result == "KNXYP6F"


def test_length() -> None:
    result = validate_and_format_patient_id("K-NXYP6FF")

    assert result is False


@pytest.mark.parametrize(
    "key, expected",
    [("HT", 9), ("4NT4K", 14), ("QRJA4DRS7", 23), ("FGEET9TY7Z6S5ZG", 10)],
)
def test_derived_remainders(key: str, expected: int) -> None:
    result = (__get_remainder(key, 2), __get_remainder(key, 1))

    assert result[0] == expected
    assert result[1] == 0
