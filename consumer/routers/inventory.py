# See https://snipe-it.readme.io/reference
from fastapi import APIRouter, HTTPException
import os
import requests

from consumer.config import config

router = APIRouter()

headers={"Authorization": f'Bearer {config.inventory_token}'}

@router.get('/users')
async def users():
    get_users_response = requests.get(
        f"{config.inventory_base_url}users",
        headers=headers)
    if 400 <= get_users_response.status_code < 500:
        raise HTTPException(
            status_code=get_users_response.status_code,
            detail="General Error")
    users_list = get_users_response.json()["rows"]
    usernames = list(map(lambda user: user["username"], users_list))
    patient_ids = list(filter(lambda name: name[1] == "-", usernames))
    return patient_ids