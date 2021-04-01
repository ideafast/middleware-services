from pathlib import Path

import pytest
import requests
import requests_mock

from data_transfer import utils
from data_transfer.config import config
from data_transfer.services import ucam

folder = Path(__file__).parent


@pytest.fixture(scope="function")
def mock_data() -> None:
    """
    Overrides configuration to use mock data
    """
    ucam.config.ucam_data = Path(f"{folder}/data/mock_ucam_db.csv")


@pytest.fixture(scope="function")
def mock_inventory_devices_bytype() -> dict:
    return utils.read_json(Path(f"{folder}/data/inventory/mock_devices_bytype.json"))


@pytest.fixture
def mock_inventory_requests() -> dict:
    inventory_history_response = utils.read_json(
        Path(f"{folder}/data/mock_inventory_history.json")
    )
    session = requests.Session()
    adapter = requests_mock.Adapter()

    config.inventory_api = f"mock://{config.inventory_api[len('http://'):]}"

    # mocks _device_history
    get_history = adapter.register_uri(
        "GET",
        f"{config.inventory_api}device/history/BTF-123456",
        json=inventory_history_response,
        status_code=200,
    )

    session.mount("mock://", adapter)
    return {"session": session, "get_history": get_history}
