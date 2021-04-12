import json
from pathlib import Path
from typing import Any

import pytest

from data_transfer import utils

folder = Path(__file__).parent


def read_json(filepath: Path) -> Any:
    with open(filepath, "r") as f:
        data = f.read()
    return json.loads(data)


@pytest.fixture(scope="function")
def mock_data() -> dict:
    return read_json(Path(f"{folder}/data/mock_consumer_ucam.json"))


@pytest.fixture(scope="function")
def mock_payload() -> dict:
    return {"data": [], "meta": {"success": True, "errors": None}}


@pytest.fixture(scope="function")
def mock_inventory_devices_bytype_response() -> dict:
    return utils.read_json(Path(f"{folder}/data/inventory/devices_bytype.json"))


@pytest.fixture(scope="function")
def mock_inventory_history_response() -> dict:
    return utils.read_json(Path(f"{folder}/data/inventory/history.json"))
