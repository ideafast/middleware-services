from consumer.main import consumer
from consumer.services import inventory
from consumer.routers import inventory as router_inventory

import pytest


def test_device_serial_correct_id(serial_response, client, monkeypatch):
    # Arrange
    async def mock_get(path: str, params: str = None):
        return serial_response
    monkeypatch.setattr(inventory, "response", mock_get)
    # Act
    res = client.get("/inventory/device/byserial/VALID_ID")
    # Assert
    assert res.json()['meta']['success'] == True


def test_device_serial_incorrect_id(serial_response, client, monkeypatch):
    async def mock_get(path: str, params: str = None):
        serial_response.update({'total': 0, 'rows': []})
        return serial_response

    monkeypatch.setattr(inventory, "response", mock_get)
    res = client.get("/inventory/device/byserial/INVALID_ID").json()
    assert len(res['meta']['errors']) > 0


def test_device_serial_multiple_devices(serial_response, client, monkeypatch):
    async def mock_get(path: str, params: str = None):
        # d1, d2 = serial_response, serial_response
        row = serial_response['rows'][0].copy()
        row.update({'asset_tag': 'SMP-SERIAL', 'checkout_counter': 9001})
        serial_response['rows'].append(row)
        return serial_response

    monkeypatch.setattr(inventory, "response", mock_get)
    res = client.get("/inventory/device/byserial/VALID_ID").json()
    assert res['data']['device_id'] == 'SMP-SERIAL'


def test_device_id_valid(response_row, client, monkeypatch):
    async def mock_get(path: str, params: str = None):
        return response_row

    monkeypatch.setattr(inventory, "response", mock_get)
    res = client.get("/inventory/device/byid/VALID_ID").json()
    assert res['data']['device_id'] == 'SMP-TEST'


def test_device_id_not_found(response_row, client, monkeypatch):
    async def mock_get(path: str, params: str = None):
        response_row['status'] = 'error'
        response_row['messages'] = 'Asset not found'
        return response_row

    monkeypatch.setattr(inventory, "response", mock_get)
    res = client.get("/inventory/device/byid/VALID_ID")

    assert res.status_code == 404
    assert res.json()['meta']['errors'][0] == response_row['messages']


def test_device_history_with_device_in_use(response_row, device_history, client, monkeypatch):
    async def mock_device_by_id(device_id: str):
        return router_inventory.serialize_device(response_row)

    monkeypatch.setattr(router_inventory, "device_by_id", mock_device_by_id)

    async def mock_get(path: str, params: str = None):
        return device_history

    monkeypatch.setattr(inventory, "response", mock_get)
    data = client.get("/inventory/device/history/VALID_ID").json()['data']

    assert data['T-123']['checkout'] and not data['T-123']['checkin']
    assert data['T-456']['checkout'] and data['T-456']['checkin']
