import json
import typing
from fastapi import Response


class CustomResponse(Response):
    media_type = "application/json"

    def envelope(self, content: typing.Any) -> dict:
        errors = []
        return {
            "data": content if not errors else None,
            "meta": {
                "success": self.status_code in [200, 201, 204],
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


def dataFromJson(fname: str):
    with open(fname) as content:
        data = json.load(content)
    return data


def mock_data_path(name: str) -> str:
    return f'./consumer/mock-data/{name}.json'
