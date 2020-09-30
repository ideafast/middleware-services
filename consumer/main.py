import uvicorn
from fastapi import FastAPI

from consumer.routers import devices, auth
from consumer.utils.general import CustomResponse

consumer = FastAPI(default_response_class=CustomResponse)
consumer.include_router(devices.router)
consumer.include_router(auth.router)


def main():
    uvicorn.run(
        "consumer.main:consumer",
        host="0.0.0.0",
        port=8000,
        reload=True)


if __name__ == "__main__":
    main()
