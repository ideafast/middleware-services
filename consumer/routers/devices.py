from fastapi import APIRouter

from consumer.utils.general import dataFromJson, mock_data_path
from consumer.models.devices import VerifyToken


router = APIRouter()


@router.get('/devices')
async def devices():
    return dataFromJson(mock_data_path('devices'))


@router.get('/devices/{device_id}/metrics')
async def metrics(device_id: str):
    return dataFromJson(mock_data_path('metrics'))


@router.get('/devices/{device_id}/status')
async def status(device_id: str):
    return dataFromJson(mock_data_path('status'))


@router.post('/verify')
async def verify(token: VerifyToken):
    return dataFromJson(mock_data_path('verification'))

