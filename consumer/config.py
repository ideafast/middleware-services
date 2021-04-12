from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseSettings


class Settings(BaseSettings):
    inventory_base_url: str = ""
    inventory_token: str = ""
    module_name: str = "consumer.main"
    variable_name: str = "consumer"
    log_level: str = ""
    support_base_url: str = ""
    support_token: str = ""
<<<<<<< HEAD
=======

    # UCAM API
    ucam_uri: str = ""
    ucam_username: str = ""
    ucam_password: str = ""
>>>>>>> 5c24f58... squash commits


@lru_cache()
def settings() -> Settings:
    load_dotenv(".consumer.env")
    return Settings()


# Create singleton for accessing configuration
config = settings()
