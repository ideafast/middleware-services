import json
import typing
from fastapi import Response


class CustomResponse(Response):
    media_type = "application/json"

    def envelope(self, content: typing.Any) -> dict:
        # Only when an HTTP/CustomException is thrown content is {errors: []}
        is_errors = isinstance(content, dict) and 'errors' in content
        errors = content['errors'] if is_errors else []
        return {
            "data": content if not errors else None,
            "meta": {
                "success": self.status_code in [200, 201, 204],
                "errors": errors or None
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


def dataFromJson(name: str):
    file_name = f'./consumer/mock-data/{name}.json'
    with open(file_name) as content:
        data = json.load(content)
    return data
