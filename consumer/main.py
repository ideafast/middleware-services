import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv, find_dotenv

from consumer.routers import auth, devices, inventory, support
from consumer.utils.general import CustomResponse


load_dotenv(find_dotenv())
consumer = FastAPI(default_response_class=CustomResponse)
consumer.include_router(auth.router)
consumer.include_router(devices.router)
consumer.include_router(inventory.router, prefix="/inventory")
consumer.include_router(support.router, prefix="/support")


def main():
    uvicorn.run(
        "consumer.main:consumer",
        host="0.0.0.0",
        port=8000,
        reload=True)


if __name__ == "__main__":
    main()
