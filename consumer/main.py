import uvicorn
from fastapi import FastAPI

from consumer.routers import devices
from consumer.utils.general import CustomResponse

consumer = FastAPI(default_response_class=CustomResponse)
consumer.include_router(devices.router)


def main():
    uvicorn.run(
        "consumer.main:consumer",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=2)


if __name__ == "__main__":
    main()
