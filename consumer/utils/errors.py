import json
import typing
from .general import CustomResponse


class CustomException(Exception):
    """
    Usage:
        raise CustomException(errors=["INVALID_TOKEN"], status_code=401)
    """
    def __init__(self, errors: str, status_code: str = 400):
        self.errors = errors
        self.status_code = status_code


async def http_error_handler(request, exc):
    """General errors handled by server, e.g. 404, 500, etc."""
    return CustomResponse({"errors":  [exc.detail]}, status_code=exc.status_code)


async def custom_error_handler(request, exc):
    """Called when we want to return specific error codes, e.g. USER_404."""
    return CustomResponse({"errors": exc.errors}, status_code=exc.status_code)
