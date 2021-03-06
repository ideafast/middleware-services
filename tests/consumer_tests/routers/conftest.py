import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from consumer.main import consumer

folder = Path(__file__).parent


def read_json(filepath: Path) -> Any:
    with open(filepath, "r") as f:
        data = f.read()
    return json.loads(data)


@pytest.fixture(scope="function")
def mock_data() -> dict:
    return read_json(Path(f"{folder}/data/mock_ucam.json"))


@pytest.fixture(scope="module")
def client():
    client = TestClient(consumer)
    yield client


@pytest.fixture(scope="function")
def response_row():
    """
    Mock data for external inventory (snipe-it) endpoint: /history/
    This is only a subset of a response that is used in the middleware.
    """
    yield {
        "asset_tag": "SMP-TEST",
        "model": {"name": "TestName"},
        "manufacturer": {"name": "SmallCo"},
        "status_label": {"status_meta": "deployed"},
        "location": {"name": "Kiel"},
        "serial": "119202",
        "id": 1123,
    }


@pytest.fixture(scope="function")
def device_history():
    """
    Mock data for external inventory (snipe-it) endpoint: /history/
    This is only a subset of a response that is used in the middleware.
    """
    yield {
        "total": 5,
        "rows": [
            {
                "created_at": {
                    "datetime": "2020-11-24 15:22:39",
                },
                "target": {
                    "name": "T-123 ",
                },
            },
            {
                "created_at": {
                    "datetime": "2020-11-25 09:37:36",
                },
                "target": {
                    "name": "T-456 ",
                },
            },
            {
                "created_at": {
                    "datetime": "2020-11-10 11:24:03",
                },
                "target": {
                    "name": "T-456 ",
                },
            },
            {
                "created_at": {
                    "datetime": "2020-11-10 11:24:04",
                },
                "target": {
                    "name": "T-456 ",
                },
            },
            {
                "created_at": {
                    "datetime": "2020-07-29 11:45:17",
                },
                "target": None,
            },
        ],
    }


@pytest.fixture(scope="function")
def serial_response():
    """
    Mock data for external inventory (snipe-it) endpoint: /byserial/
    This is only a subset of a response that is used in the middleware.
    """
    response = {
        "total": 1,
        "rows": [
            {
                "id": 0,
                "asset_tag": "SMP-ABC123",
                "serial": "S13SF2M112",
                "model": {"name": "Samsung Galaxy A40"},
                "status_label": {"status_meta": "deployed"},
                "manufacturer": {"name": "Samsung"},
                "location": {"name": "Newcastle"},
                "checkout_counter": 1,
            }
        ],
    }
    yield response
