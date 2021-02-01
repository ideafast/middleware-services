from pathlib import Path
from data_transfer.services import ucam

import pytest


@pytest.fixture(scope="function")
def mock_data():
    """
    Overrides configuration to use mock data 
    """
    folder = Path(__file__).parent
    ucam.config.ucam_data = f"{folder}/data/mock_ucam_db.csv"