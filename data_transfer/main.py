import logging
import os

from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every

from .jobs import example

logger = logging.getLogger(__name__)

data_transfer = FastAPI()


@data_transfer.on_event("startup")
@repeat_every(seconds=1, logger=logger, wait_first=True)
def print_time():
    example.run_job()