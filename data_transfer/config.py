from pydantic import BaseSettings
from functools import lru_cache
from dotenv import load_dotenv
from pathlib import Path

import os


load_dotenv('.dtransfer.env')


# TODO: would be docker volume
root_path = Path(__file__).parent.parent


class Settings(BaseSettings):
    database_uri: str

    dreem_users: Path = root_path / 'ideafast-users-full.csv'
    dreem_devices: Path = root_path / 'ideafast-devices-full.csv'

    ucam_data: Path = root_path / 'ucam_db.csv'
    
    storage_vol: Path = root_path / 'data/input'
    upload_folder: Path = root_path / 'data/uploading'

    inventory_api: str

    support_base_url: str
    support_token: str

    # NOTE: VTT does not differentiate between study sites
    vttsma_aws_accesskey: str
    vttsma_aws_secret_accesskey: str
    vttsma_aws_bucket_name: str

    dreem_login_url: str
    dreem_api_url: str

    # Hardcoded as this data structure is not
    # supported unless JSON is stored in .env
    dreem: dict = {
        "kiel": (
            os.getenv("DREEM_KIEL_USERNAME"),
            os.getenv("DREEM_KIEL_PASSWORD")
        ),
        "newcastle": (
            os.getenv("DREEM_NEWCASTLE_USERNAME"),
            os.getenv("DREEM_NEWCASTLE_PASSWORD")
        ),
        "munster": (
            os.getenv("DREEM_MUNSTER_USERNAME"),
            os.getenv("DREEM_MUNSTER_PASSWORD")
        ),
        "rotterdam": (
            os.getenv("DREEM_ROTTERDAM_USERNAME"),
            os.getenv("DREEM_ROTTERDAM_PASSWORD")
        )
    }

@lru_cache()
def settings() -> Settings:
    return Settings()

config = settings()