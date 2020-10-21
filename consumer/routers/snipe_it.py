from fastapi import APIRouter
import os
import requests


router = APIRouter()
bearer_token = os.getenv("SNIPE_IT_TOKEN")
headers = {"Accept": "application/json", "Content-Type": "application/json", "Authorization": f'Bearer {bearer_token}'}
# See https://snipe-it.readme.io/reference for full Snipe-IT API reference


@router.get('/users')
async def users():
    get_hardware = requests.get(
        "https://inventory.ideafast.eu/api/v1/hardware?status=&order_number=&company_id=&status_id=&sort=name&order=asc&offset=0&limit=20",
        headers=headers)
    return get_hardware.text
