import json
import typing
import uvicorn
from fastapi import FastAPI, Response


class CustomResponse(Response):
    def envelope(self, content: typing.Any) -> dict:
        errors = []
        return {
            "data": content if not errors else None,
            "meta": {
                "success": self.status_code in [200, 201, 204],
                "code": self.status_code,
                "errors": errors
            }
        }

    def render(self, content: typing.Any) -> bytes:
        return json.dumps(
            self.envelope(content),
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")


consumer = FastAPI(default_response_class=CustomResponse)


def dataFromJson(fname: str):
    with open(fname) as content:
        data = json.load(content)
    return data


def mock_data_path(name):
    return f'./consumer/mock-data/{name}.json'

@consumer.get('/devices')
async def devices(response: Response):
    return dataFromJson(mock_data_path('devices'))


@consumer.get('/devices/{device_id}/metrics')
async def metrics(device_id: str):
    return dataFromJson(mock_data_path('metrics'))


@consumer.get('/devices/{device_id}/status')
async def status(device_id: str):
    return dataFromJson(mock_data_path('status'))


@consumer.get('/verify')
async def verify():
    return dataFromJson(mock_data_path('verification'))


def main():
    uvicorn.run("consumer.main:consumer", host="0.0.0.0", port=8000, reload=True, workers=2)


if __name__ == "__main__":
    main()
