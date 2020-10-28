import uvicorn
import os
from fastapi import FastAPI
from dotenv import load_dotenv, find_dotenv

from consumer.routers import auth, devices, inventory, support
from consumer.utils.general import CustomResponse

load_dotenv(find_dotenv('.consumer.env'))
access_authenticated_endpoints = os.getenv("ACCESS_AUTHENTICATED_ENDPOINTS")
module_name = os.getenv("MODULE_NAME")
variable_name = os.getenv("VARIABLE_NAME")
consumer = FastAPI(default_response_class=CustomResponse)
consumer.include_router(auth.router)
consumer.include_router(devices.router)
if bool(access_authenticated_endpoints):
    consumer.include_router(inventory.router, prefix="/inventory")
    consumer.include_router(support.router, prefix="/support")


def main():
    uvicorn.run(
        f"{module_name}:{variable_name}",
        host="0.0.0.0",
        port=8000,
        reload=True)


if __name__ == "__main__":
    main()
