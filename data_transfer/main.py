import uvicorn
from fastapi import FastAPI

from data_transfer.jobs import example

data_transfer = FastAPI()
data_transfer.include_router(example.router)


def main():
    uvicorn.run(
        "data_transfer.main:data_transfer",
        host="0.0.0.0",
        port=8001,
        reload=True)


if __name__ == "__main__":
    main()
