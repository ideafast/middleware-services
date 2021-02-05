from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseSettings

load_dotenv(".consumer.env")


class Settings(BaseSettings):
    inventory_base_url: str
    inventory_token: str
    module_name: str = "consumer.main"
    variable_name: str = "consumer"
    log_level: str
    support_base_url: str
    support_token: str
    access_authenticated_endpoints: bool


@lru_cache()
def settings() -> Settings:
    return Settings()


# Create singleton for accessing configuration
config = settings()
