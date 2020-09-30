from fastapi import APIRouter

from consumer.utils.general import dataFromJson
from consumer.models.devices import VerifyToken


router = APIRouter()


@router.get('/devices')
async def devices():
    return dataFromJson('devices')


@router.get('/devices/{device_id}/metrics')
async def metrics(device_id: str):
    return dataFromJson('metrics')


@router.get('/devices/{device_id}/status')
async def status(device_id: str):
    return dataFromJson('status')


@router.post('/verify')
async def verify(token: VerifyToken):
    return dataFromJson('verification')

