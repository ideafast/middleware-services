FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8-alpine3.10

RUN apk add --no-cache curl

# Install Poetry
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

WORKDIR /app/
COPY ./ /app/

RUN poetry install --no-root --no-dev
