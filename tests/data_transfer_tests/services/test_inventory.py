from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

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


def test_all_devices_by_type_cache_success() -> None:
    inventory.all_devices_by_type.cache_clear()
    num_requests = 10

    with patch("requests.get", return_value=Mock()) as _:
        for __ in range(0, num_requests):
            inventory.all_devices_by_type(utils.DeviceType.BTF)

        result = inventory.all_devices_by_type.cache_info()

        assert result[1] == 1  # first request is cached
        assert result[0] == num_requests - 1


def test_device_id_by_serial_valid_result(
    mock_inventory_devices_bytype: dict,
) -> None:
    inventory.all_devices_by_type.cache_clear()
    response = MagicMock()
    response.json = lambda: mock_inventory_devices_bytype

    with patch("requests.get", return_value=response) as _:

        result = inventory.device_id_by_serial(utils.DeviceType.BTF, "ABC456")

        assert result == "BTF-K93DTY"


def test_device_id_by_serial_hit_cache_success(
    mock_inventory_devices_bytype: dict,
) -> None:
    inventory.all_devices_by_type.cache_clear()
    num_requests = 10
    response = MagicMock()
    response.json = lambda: mock_inventory_devices_bytype

    with patch("requests.get", return_value=response) as _:
        for __ in range(0, num_requests):
            inventory.all_devices_by_type(utils.DeviceType.BTF)

        result = inventory.all_devices_by_type.cache_info()

        assert result[0] == num_requests - 1
