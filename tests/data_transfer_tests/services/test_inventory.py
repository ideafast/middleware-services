from unittest.mock import MagicMock, patch

from data_transfer import utils
from data_transfer.services import inventory


def test_record_by_device_id_date_within(
    mock_inventory_history_response: dict, mock_inv_config: MagicMock
) -> None:
    response = MagicMock()
    response.json = lambda: mock_inventory_history_response

    with patch("requests.get", return_value=response):
        start_wear = utils.format_weartime("2021-03-22 12:11:55", "inventory")
        end_wear = utils.format_weartime("2021-03-22 22:11:55", "inventory")

        result = inventory.record_by_device_id("BTF-123456", start_wear, end_wear)[
            "patient_id"
        ]

        assert result == "A-ABCDEF"


def test_record_by_device_id_history_is_none(
    mock_inventory_history_response: dict,
    mock_inv_config: MagicMock,
) -> None:
    response = MagicMock()
    response.json = lambda: mock_inventory_history_response

    with patch("requests.get", return_value=response):
        start_wear = utils.format_weartime("2021-03-17 12:11:55", "inventory")
        end_wear = utils.format_weartime("2021-03-17 22:11:55", "inventory")

        result = inventory.record_by_device_id("BTF-123456", start_wear, end_wear)

        assert result is None


def test_device_history_failure(
    mock_inventory_history_response: dict,
    mock_inv_config: MagicMock,
) -> None:
    inventory.device_history.cache_clear()
    response = MagicMock()
    mock_inventory_history_response["meta"]["success"] = False
    response.json = lambda: mock_inventory_history_response

    with patch("requests.get", return_value=response):

        result = inventory.device_history("BTF-123456")

        assert result is None


def test_device_history_success(
    mock_inventory_history_response: dict,
    mock_inv_config: MagicMock,
) -> None:
    inventory.device_history.cache_clear()
    response = MagicMock()
    response.json = lambda: mock_inventory_history_response

    with patch("requests.get", return_value=response):

        result = inventory.device_history("BTF-123456")

        assert "A-ABCDEF" in result


def test_record_by_device_id_date_outside(
    mock_inventory_history_response: dict,
    mock_inv_config: MagicMock,
) -> None:
    response = MagicMock()
    response.json = lambda: mock_inventory_history_response

    with patch("requests.get", return_value=response):
        start_wear = utils.format_weartime("2021-03-17 12:11:55", "inventory")
        end_wear = utils.format_weartime("2021-03-17 22:11:55", "inventory")

        result = inventory.record_by_device_id("BTF-123456", start_wear, end_wear)

        assert result is None


def test_all_devices_by_type_cache_success(mock_inv_config: MagicMock) -> None:
    inventory.all_devices_by_type.cache_clear()
    num_requests = 10

    with patch("requests.get", return_value=MagicMock()) as get:
        for __ in range(0, num_requests):
            inventory.all_devices_by_type(utils.DeviceType.BTF)

        get.assert_called_once()  # Act


def test_device_id_by_serial_valid_result(
    mock_inventory_devices_bytype_response: dict, mock_inv_config: MagicMock
) -> None:
    inventory.all_devices_by_type.cache_clear()
    response = MagicMock()
    response.json = lambda: mock_inventory_devices_bytype_response

    with patch("requests.get", return_value=response):

        result = inventory.device_id_by_serial(utils.DeviceType.BTF, "ABC456")

        assert result == "BTF-TEST01"


def test_device_id_by_serial_hit_cache_success(
    mock_inventory_devices_bytype_response: dict, mock_inv_config: MagicMock
) -> None:
    inventory.all_devices_by_type.cache_clear()
    num_requests = 10
    response = MagicMock()
    response.json = lambda: mock_inventory_devices_bytype_response

    with patch("requests.get", return_value=response):
        for _ in range(0, num_requests):
            inventory.all_devices_by_type(utils.DeviceType.BTF)

        result = inventory.all_devices_by_type.cache_info()

        assert result[0] == num_requests - 1
