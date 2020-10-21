from fastapi import APIRouter

from consumer.utils.general import dataFromJson
from consumer.schemas.token import VerifyToken

router = APIRouter()


@router.get('/users')
async def users():
    return 'SNIPE-IT USERS'
