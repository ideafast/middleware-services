from fastapi import FastAPI
from requests import RequestException
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import config
from .routers import auth, devices, inventory, support
from .utils.errors import (
    CustomException,
    custom_error_handler,
    http_error_handler,
    http_error_handler_requests,
)
from .utils.general import CustomResponse

consumer = FastAPI(default_response_class=CustomResponse)

consumer.include_router(auth.router)
consumer.include_router(devices.router)

if config.access_authenticated_endpoints:
    consumer.include_router(inventory.router, prefix="/inventory")
    consumer.include_router(support.router, prefix="/support")

consumer.add_exception_handler(StarletteHTTPException, http_error_handler)
consumer.add_exception_handler(RequestException, http_error_handler_requests)
consumer.add_exception_handler(CustomException, custom_error_handler)
