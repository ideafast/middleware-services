import uvicorn
import logging
import time
from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every

logger = logging.getLogger(__name__)
app = FastAPI()
counter = 0

@app.on_event("startup")
@repeat_every(seconds=1, logger=logger, wait_first=True)
def periodic():
    global counter
    print('counter is', counter)
    counter += 1
    # Run file

def main():
    uvicorn.run(
        "data_transfer.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True)


if __name__ == "__main__":
    main()
