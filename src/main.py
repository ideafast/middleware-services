import json
import typing
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


app = FastAPI(default_response_class=CustomResponse)


def dataFromJson(fname: str):
    with open(fname) as content:
        data = json.load(content)
    return data


@app.get('/devices')
async def devices(response: Response):
    return dataFromJson('devices.json')


@app.get('/devices/{device_id}/metrics')
async def metrics(device_id: str):
    return dataFromJson('metrics.json')


@app.get('/devices/{device_id}/status')
async def status(device_id: str):
    return dataFromJson('status.json')


@app.get('/verify')
async def verify():
    return dataFromJson('verification.json')
