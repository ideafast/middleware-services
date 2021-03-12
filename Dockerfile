FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-alpine3.10 as base

ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1

FROM base as builder

RUN apk add --quiet --no-cache --virtual .build-deps gcc libffi-dev musl-dev postgresql-dev \
    && pip install -q poetry \
    && apk del .build-deps

COPY pyproject.toml poetry.lock ./
RUN poetry export --without-hashes > /tmp/requirements.txt

FROM base as final

COPY . /app/
COPY --from=builder /tmp/requirements.txt /app/

RUN apk add --quiet --no-cache --virtual .deps gcc libffi-dev musl-dev postgresql-dev git \
    && pip install --quiet -r /app/requirements.txt \
    && apk del .deps