from .general import CustomResponse
from fastapi import Request

from starlette.exceptions import HTTPException


class CustomException(Exception):
    """
    Usage:
        raise CustomException(errors=["INVALID_TOKEN"], status_code=401)
    """

    def __init__(self, errors: list, status_code: int = 400):
        self.errors = errors
        self.status_code = status_code


async def http_error_handler(request: Request, exc: HTTPException) -> CustomResponse:
    """General errors handled by server, e.g. 404, 500, etc."""
    return CustomResponse({"errors": [exc.detail]}, status_code=exc.status_code)


async def custom_error_handler(
    request: Request, exc: CustomException
) -> CustomResponse:
    """Called when we want to return specific error codes, e.g. USER_404."""
    return CustomResponse({"errors": exc.errors}, status_code=exc.status_code)
