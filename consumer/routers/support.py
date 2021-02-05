# See https://docs.zammad.org/en/latest/api/intro.html
import requests
from fastapi import APIRouter, HTTPException

from consumer.config import config

router = APIRouter()

headers = {"Authorization": f"Bearer {config.support_token}"}


@router.get("/users")
async def users() -> list:
    get_users_response = requests.get(
        f"{config.support_base_url}users", headers=headers
    )
    if 400 <= get_users_response.status_code < 500:
        raise HTTPException(
            status_code=get_users_response.status_code, detail="General Error"
        )
    users_list = get_users_response.json()
    usernames = list(
        map(lambda user: f"{user['firstname']} {user['lastname']}", users_list)
    )
    return usernames
