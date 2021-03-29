from datetime import datetime
from unittest.mock import patch

from data_transfer import utils
from data_transfer.services import inventory


def test_date_within(mock_inventory_requests: dict) -> None:

    with patch.object(inventory, "requests", mock_inventory_requests["session"]):
        start_wear = utils.format_weartime("2021-03-22 12:11:55", "inventory")
        end_wear = utils.format_weartime("2021-03-22 22:11:55", "inventory")

        result = inventory.record_by_device_id("BTF-123456", start_wear, end_wear)[
            "patient_id"
        ]

        assert result == "A-ABCDEF"


def test_date_outside(mock_inventory_requests: dict) -> None:

    with patch.object(inventory, "requests", mock_inventory_requests["session"]):
        start_wear = utils.format_weartime("2021-03-17 12:11:55", "inventory")
        end_wear = utils.format_weartime("2021-03-17 22:11:55", "inventory")

        result = inventory.record_by_device_id("BTF-123456", start_wear, end_wear)

        assert result is None


def test_normalise_day() -> None:
    one = utils.normalise_day(datetime(2021, 3, 26, 0, 0, 0, 647241))
    two = utils.normalise_day(datetime(2021, 3, 26, 0, 0, 0, 565704))

    result = one == two

    assert result
