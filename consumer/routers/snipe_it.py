from fastapi import APIRouter
import requests

from consumer.utils.general import dataFromJson
from consumer.schemas.token import VerifyToken

router = APIRouter()


@router.get('/users')
async def users():
    r = requests.get('http://www.randomnumberapi.com/api/v1.0/random')
    print(r)
    return r.text
