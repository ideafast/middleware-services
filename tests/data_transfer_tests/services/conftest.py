from pathlib import Path

import pytest

from data_transfer.services import ucam


@pytest.fixture(scope="function")
def mock_data() -> None:
    """
    Overrides configuration to use mock data
    """
    folder = Path(__file__).parent
    ucam.config.ucam_data = Path(f"{folder}/data/mock_ucam_db.csv")