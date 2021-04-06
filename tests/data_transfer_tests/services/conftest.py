from pathlib import Path

import pytest

from data_transfer import utils
from data_transfer.services import ucam

folder = Path(__file__).parent


@pytest.fixture(scope="function")
def mock_data() -> None:
    """
    Overrides configuration to use mock data
    """
    ucam.config.ucam_data = Path(f"{folder}/data/mock_ucam_db.csv")


@pytest.fixture(scope="function")
def mock_inventory_devices_bytype_response() -> dict:
    return utils.read_json(Path(f"{folder}/data/inventory/devices_bytype.json"))


@pytest.fixture(scope="function")
def mock_inventory_history_response() -> dict:
    return utils.read_json(Path(f"{folder}/data/inventory/history.json"))
