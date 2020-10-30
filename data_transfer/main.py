import logging
import os
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
from dotenv import load_dotenv, find_dotenv

from .jobs import example

logger = logging.getLogger(__name__)
load_dotenv(find_dotenv('.dtransfer.env'))
module_name = os.getenv("MODULE_NAME")
variable_name = os.getenv("VARIABLE_NAME")
data_transfer = FastAPI()


@data_transfer.on_event("startup")
@repeat_every(seconds=1, logger=logger, wait_first=True)
def print_time():
    example.run_job()