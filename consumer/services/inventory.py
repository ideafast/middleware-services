import requests
import json

from consumer.config import config


def response(path: str, params: str = None) -> json:
    """Helper method to share validation across requests."""
    headers = {"Authorization": f'Bearer {config.inventory_token}'}
    url = f"{config.inventory_base_url}/{path}"
    res = requests.get(url, params=params, headers=headers)

    # snipe-it returns a login page (html) when this is the case.
    if 'text/html' in res.headers.get('content-type', ''):
        raise CustomException(
            errors=['Invalid inventory configuration.'],
            status_code=401)
    return res.json()
