from datetime import datetime

import pytest

from data_transfer.utils import (
    __format_id_ideafast,
    __get_remainder,
    format_id_device,
    format_id_patient,
    normalise_day,
)


def test_patient_valid() -> None:
    result = format_id_patient("K-NXYP6F")

    assert result == "K-NXYP6F"


def test_device_valid() -> None:
    result = format_id_device("ABC-FYCRXH")

    assert result == "ABC-FYCRXH"


def test_device_ideafast_valid_no_prefix() -> None:
    result = __format_id_ideafast("FYCRXH", 0)

    assert result == "-FYCRXH"  # Note the prepended - due to expected prefixes


def test_device_ideafast_valid() -> None:
    result = __format_id_ideafast("ABC-FYCRXH", 3)

    assert result == "ABC-FYCRXH"


def test_weard_prefix_ideafast_valid() -> None:
    result = __format_id_ideafast("AbCDef129A-FYCRXH", 10)

    assert result == "ABCDEF129A-FYCRXH"


def test_device_ideafast_invalid() -> None:
    result = __format_id_ideafast("FYCRXW", 1)

    assert result is None


def test_invalid() -> None:
    result = format_id_patient("K-NXyP6G")

    assert result is None


def test_punctuation() -> None:
    result = format_id_patient("K-NXYP6F.")

    assert result == "K-NXYP6F"


def test_tabs_spaces() -> None:
    result = format_id_patient("K-N XYP6\tF ")

    assert result == "K-NXYP6F"


def test_lower_case() -> None:
    result = format_id_patient("knxyp6f")

    assert result == "K-NXYP6F"


def test_length_patient() -> None:
    result = format_id_patient("K-NXYP6FF")

    assert result is None


def test_length_device() -> None:
    result = format_id_device("K-NXYP6FF")

    assert result is None


@pytest.mark.parametrize(
    "key, expected",
    [("HT", 9), ("4NT4K", 14), ("QRJA4DRS7", 23), ("FGEET9TY7Z6S5ZG", 10)],
)
def test_derived_remainders(key: str, expected: int) -> None:
    result = (__get_remainder(key, 2), __get_remainder(key, 1))

    assert result[0] == expected
    assert result[1] == 0


def test_normalise_day() -> None:
    one = normalise_day(datetime(2021, 3, 26, 0, 0, 0, 647241))
    two = normalise_day(datetime(2021, 3, 26, 0, 0, 0, 565704))

    result = one == two

    assert result
