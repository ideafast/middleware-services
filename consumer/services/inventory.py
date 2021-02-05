import json
from typing import Any

import requests

from consumer.config import config
from consumer.utils.errors import CustomException


async def response(path: str, params: str = None) -> Any:
    """Helper method to share validation across requests."""
    headers = {"Authorization": f"Bearer {config.inventory_token}"}
    url = f"{config.inventory_base_url}/{path}"
    res = requests.get(url, params=params, headers=headers)

    if res.status_code == 429:
        raise CustomException(errors=["Rate Limit on API access."], status_code=429)

    # snipe-it returns a login page (html) on error
    if "text/html" in res.headers.get("content-type", ""):
        raise CustomException(
            errors=["Invalid inventory configuration."], status_code=401
        )
    return res.json()
