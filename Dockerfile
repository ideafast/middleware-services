FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-alpine3.10 as base

FROM base as builder

ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1

RUN apk add --no-cache gcc libffi-dev musl-dev postgresql-dev
RUN pip -q install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry export --without-hashes -o requirements.txt > /tmp/requirements.txt

FROM base as final

COPY . /app/
COPY --from=builder /tmp/requirements.txt /app/

RUN pip install --quiet -r /app/requirements.txt
