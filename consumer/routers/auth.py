from typing import Any

from fastapi import APIRouter

from consumer.schemas.token import VerifyToken
from consumer.utils.general import dataFromJson

router = APIRouter()


@router.post("/verify")
async def verify(token: VerifyToken) -> Any:
    return dataFromJson("verification")
