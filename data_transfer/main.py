import uvicorn
import logging
import os
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from dotenv import load_dotenv, find_dotenv

from data_transfer.jobs import dmp, example

logger = logging.getLogger(__name__)
load_dotenv(find_dotenv('.dtransfer.env'))
module_name = os.getenv("MODULE_NAME")
variable_name = os.getenv("VARIABLE_NAME")
data_transfer = FastAPI()
data_transfer.include_router(dmp.router, prefix="/dmp")


@data_transfer.on_event("startup")
@repeat_every(seconds=3600, logger=logger, wait_first=True)
def print_time():
    dmp.run_job()
    # example.run_job()


def main():
    uvicorn.run(
        f"{module_name}:{variable_name}",
        host="0.0.0.0",
        port=8001,
        reload=True)


if __name__ == "__main__":
    main()
