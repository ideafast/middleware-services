FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-alpine3.10 as base


FROM base as builder

RUN apk add --no-cache gcc libffi-dev musl-dev postgresql-dev
RUN pip -q install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt > /tmp/requirements.txt

FROM base as final

WORKDIR /app/

COPY . /app/
COPY --from=builder /tmp/requirements.txt /app/

RUN pip install --quiet -r /app/requirements.txt
