from fastapi import APIRouter
import json
import os
import requests


router = APIRouter()
bearer_token = os.getenv("SNIPE_IT_TOKEN")
headers = {"Accept": "application/json", "Content-Type": "application/json", "Authorization": f'Bearer {bearer_token}'}
# See https://snipe-it.readme.io/reference for full Snipe-IT API reference


@router.get('/users')
async def users():
    get_users_request = requests.get(
        "https://inventory.ideafast.eu/api/v1/users",
        headers=headers)
    all_users = json.loads(get_users_request.text)["rows"]
    return all_users[0]
