import pytest

from consumer.routers import inventory as router_inventory
from consumer.schemas.inventory import Device
from consumer.services import inventory


def test_device_serial_correct_id(serial_response, client, monkeypatch) -> None:
    async def mock_get(path: str, params: str = None):
        return serial_response

    monkeypatch.setattr(inventory, "response", mock_get)

    result = client.get("/inventory/device/byserial/VALID_ID").json()["meta"]["success"]

    assert result is True


def test_device_serial_no_location(serial_response, client, monkeypatch) -> None:
    async def mock_get(path: str, params: str = None):
        serial_response["rows"][0]["location"] = None
        return serial_response

    monkeypatch.setattr(inventory, "response", mock_get)

    result = client.get("/inventory/device/byserial/VALID_ID").json()["meta"]["success"]

    assert result is True


def test_device_serial_incorrect_id(serial_response, client, monkeypatch) -> None:
    async def mock_get(path: str, params: str = None):
        serial_response.update({"total": 0, "rows": []})
        return serial_response

    monkeypatch.setattr(inventory, "response", mock_get)

    result = client.get("/inventory/device/byserial/INVALID_ID").json()

    assert len(result["meta"]["errors"]) > 0


def test_device_serial_multiple_devices(serial_response, client, monkeypatch) -> None:
    async def mock_get(path: str, params: str = None):
        row = serial_response["rows"][0].copy()
        row.update({"asset_tag": "SMP-SERIAL", "checkout_counter": 9001})
        serial_response["rows"].append(row)
        return serial_response

    monkeypatch.setattr(inventory, "response", mock_get)

    result = client.get("/inventory/device/byserial/VALID_ID").json()

    assert result["data"]["device_id"] == "SMP-SERIAL"


def test_device_id_valid(response_row, client, monkeypatch) -> None:
    async def mock_get(path: str, params: str = None):
        return response_row

    monkeypatch.setattr(inventory, "response", mock_get)

    result = client.get("/inventory/device/byid/VALID_ID").json()

    assert result["data"]["device_id"] == "SMP-TEST"


def test_device_id_not_found(response_row, client, monkeypatch) -> None:
    async def mock_get(path: str, params: str = None):
        response_row["status"] = "error"
        response_row["messages"] = "Asset not found"
        return response_row

    monkeypatch.setattr(inventory, "response", mock_get)

    result = client.get("/inventory/device/byid/VALID_ID")

    assert result.status_code == 404
    assert result.json()["meta"]["errors"][0] == response_row["messages"]


def test_device_history_with_device_in_use_success(
    response_row, device_history, client, monkeypatch
) -> None:
    async def mock_device_by_id(device_id: str):
        return Device.serialize(response_row)

    monkeypatch.setattr(router_inventory, "device_by_id", mock_device_by_id)

    async def mock_get(path: str, params: str = None):
        return device_history

    monkeypatch.setattr(inventory, "response", mock_get)

    result = client.get("/inventory/device/history/VALID_ID").json()["data"]

    assert result["T-123"]["checkout"] and not result["T-123"]["checkin"]
    assert result["T-456"]["checkout"] and result["T-456"]["checkin"]


def test_device_history_with_device_multiple_checkouts(
    response_row, device_history, client, monkeypatch
) -> None:
    async def mock_device_by_id(device_id: str):
        return Device.serialize(response_row)

    monkeypatch.setattr(router_inventory, "device_by_id", mock_device_by_id)

    async def mock_get(path: str, params: str = None):
        return device_history

    monkeypatch.setattr(inventory, "response", mock_get)

    result = client.get("/inventory/device/history/VALID_ID").json()["data"]

    assert result["T-456"]["checkout"] == "2020-11-10 11:24:03"
    assert result["T-456"]["checkin"] == "2020-11-25 09:37:36"


@pytest.mark.parametrize("key", ["id", "serial", "asset_tag", "status_label"])
@pytest.mark.xfail(raises=KeyError, strict=True)
def test_serialize_device_required_params(key, response_row) -> None:
    del response_row[key]

    Device.serialize(response_row)  # Act


serial_optional_params = [
    ("location", "name"),
    ("model", "name"),
    ("manufacturer", "name"),
]


@pytest.mark.parametrize("key, child", serial_optional_params)
def test_device_serial_optional_params(key, child, response_row) -> None:
    del response_row[key][child]

    result = Device.serialize(response_row)

    assert not result.dict()[key]
