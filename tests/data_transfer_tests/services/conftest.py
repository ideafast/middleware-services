import json
from pathlib import Path
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest

from data_transfer import utils
from data_transfer.services import inventory, ucam

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


@pytest.fixture(scope="module")
def mock_ucam_config() -> Generator[MagicMock, None, None]:

    nconfig = MagicMock(ucam_api="mock://mock_url.com")

    with patch.object(ucam, "config", return_value=nconfig) as mockconfig:
        yield mockconfig


@pytest.fixture(scope="module")
def mock_inv_config() -> Generator[MagicMock, None, None]:

    nconfig = MagicMock(inventory_api="mock://mock_url.com")

    with patch.object(inventory, "config", return_value=nconfig) as mockconfig:
        yield mockconfig
