from fastapi import APIRouter

from consumer.utils.general import dataFromJson

router = APIRouter()


@router.get("/devices")
async def devices():
    return dataFromJson("devices")


@router.get("/devices/{device_id}/metrics")
async def metrics(device_id: str):
    return dataFromJson("metrics")


@router.get("/devices/{device_id}/status")
async def status(device_id: str):
    return dataFromJson("status")
