import os
from functools import lru_cache
from pathlib import Path

from dotenv import get_key, load_dotenv
from pydantic import BaseSettings


def get_env_value(key_to_get: str, env_file: str = ".dtransfer.prod.env") -> str:
    """Load from general env then specific file if not found."""
    return os.getenv(key_to_get) or get_key(env_file, key_to_get)


class GlobalConfig(BaseSettings):
    """Global configurations."""

    root_path = Path(__file__).parent.parent

    csvs_path = root_path / "local"
    data_path = root_path / "data"

    storage_vol: Path = data_path / "input"
    upload_folder: Path = data_path / "uploading"

    dreem_users: Path = csvs_path / "ideafast-users-full.csv"
    dreem_devices: Path = csvs_path / "ideafast-devices-full.csv"

    ucam_data: Path = csvs_path / "ucam_db.csv"


class Settings(GlobalConfig):
    is_dev: bool

    database_uri: str
    inventory_api: str

    support_base_url: str
    support_token: str

    dmp_study_id: str
    dmp_url: str
    dmp_public_key: str
    dmp_signature: str
    dmp_access_token: str
    dmp_access_token_gen_time: int

    # NOTE: VTT does not differentiate between study sites
    vttsma_aws_accesskey: str
    vttsma_aws_secret_accesskey: str
    vttsma_aws_bucket_name: str
    vttsma_global_device_id: str

    dreem_login_url: str
    dreem_api_url: str

    # Hardcoded as this data structure is not
    # supported unless JSON is stored in .env
    dreem: dict = {
        "kiel": (
            get_env_value("DREEM_KIEL_USERNAME"),
            get_env_value("DREEM_KIEL_PASSWORD"),
        ),
        "newcastle": (
            get_env_value("DREEM_NEWCASTLE_USERNAME"),
            get_env_value("DREEM_NEWCASTLE_PASSWORD"),
        ),
        "munster": (
            get_env_value("DREEM_MUNSTER_USERNAME"),
            get_env_value("DREEM_MUNSTER_PASSWORD"),
        ),
        "rotterdam": (
            get_env_value("DREEM_ROTTERDAM_USERNAME"),
            get_env_value("DREEM_ROTTERDAM_PASSWORD"),
        ),
    }


@lru_cache()
def settings() -> Settings:
    """
    Only a few services provide development environments, e.g., DMPY.
    As such, live APIs are used for most local developement and
    specific production values overriden for development.
    """
    # Load production settings as many are shared with dev.
    load_dotenv(".dtransfer.prod.env")

    if get_env_value("IS_DEV"):
        # Override specific prod values, e.g., DMP.
        load_dotenv(".dtransfer.dev.env", override=True)

    return Settings()


config = settings()
