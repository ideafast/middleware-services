from fastapi import APIRouter, HTTPException
import os
import requests


router = APIRouter()
base_url = os.getenv("INVENTORY_BASE_URL")
bearer_token = os.getenv("INVENTORY_TOKEN")
# See https://snipe-it.readme.io/reference for full Snipe-IT API reference


@router.get('/users')
async def users():
    get_users_response = requests.get(
        f"{base_url}users",
        headers={"Authorization": f'Bearer {bearer_token}'})
    if 400 <= get_users_response.status_code < 500:
        raise HTTPException(
            status_code=get_users_response.status_code,
            detail="General Error")
    users_list = get_users_response.json()["rows"]
    usernames = list(map(lambda user: user["username"], users_list))
    patient_ids = list(filter(lambda name: name[1] == "-", usernames))
    return patient_ids
