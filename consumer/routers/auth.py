from fastapi import APIRouter

from consumer.utils.general import dataFromJson
from consumer.models.devices import VerifyToken

router = APIRouter()


@router.post('/verify')
async def verify(token: VerifyToken):
    return dataFromJson('verification')

