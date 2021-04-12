from fastapi import Request
from requests import RequestException
from starlette.exceptions import HTTPException

from .general import CustomResponse


class CustomException(Exception):
    """
    Usage:
        raise CustomException(errors=["INVALID_TOKEN"], status_code=401)
    """

    __slots__ = ["errors", "status_code"]

    def __init__(self, errors: list, status_code: int = 400):
        self.errors = errors
        self.status_code = status_code


def error_response(errors: list, status_code: int) -> CustomResponse:
    return CustomResponse({"errors": errors}, status_code=status_code)


async def http_error_handler(request: Request, exc: HTTPException) -> CustomResponse:
    """General errors handled by server, e.g. 404, 500, etc."""
    return error_response([exc.detail], exc.status_code)


async def http_error_handler_requests(
    request: Request, exc: RequestException
) -> CustomResponse:
    """General errors handled for all requests errors"""
    # TODO: log that this occured, and exc.response.reason, and status_code
    reason = exc.response.reason if exc.response else "ERROR_500"
    status_code = exc.response.status_code if exc.response else 500
    return error_response([reason], status_code)


async def custom_error_handler(
    request: Request, exc: CustomException
) -> CustomResponse:
    """Called when we want to return specific error codes, e.g. USER_404."""
    return error_response(exc.errors, exc.status_code)
