from fastapi import APIRouter
import json
import os
import requests


router = APIRouter()
bearer_token = os.getenv("INVENTORY_TOKEN")
headers = {"Accept": "application/json", "Content-Type": "application/json", "Authorization": f'Bearer {bearer_token}'}
# See https://snipe-it.readme.io/reference for full Snipe-IT API reference


@router.get('/users')
async def users():
    get_users_response = requests.get(
        "https://inventory.ideafast.eu/api/v1/users",
        headers=headers)
    users_list = json.loads(get_users_response.text)["rows"]
    usernames = list(map(lambda user: user["username"], users_list))
    patient_ids = list(filter(lambda name: name[1] == "-", usernames))
    return patient_ids
