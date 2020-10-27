from fastapi import APIRouter, HTTPException
import os
import requests


router = APIRouter()
base_url = os.getenv("SUPPORT_BASE_URL")
bearer_token = os.getenv("SUPPORT_TOKEN")
# See https://docs.zammad.org/en/latest/api/intro.html for full Zammad API reference


@router.get('/users')
async def users():
    get_users_response = requests.get(
        f"{base_url}users",
        headers={"Authorization": f'Bearer {bearer_token}'})
    if 400 <= get_users_response.status_code < 500:
        raise HTTPException(
            status_code=get_users_response.status_code,
            detail="General Error")
    users_list = get_users_response.json()
    return users_list
