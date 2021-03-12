FROM python:3.8-alpine3.10 as base

# Saves having to add --no-cache-dir to pip installs
ENV PIP_NO_CACHE_DIR=1
# Causes error on pip
ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1

# Temporarily install dependencies to build/install poetry
# Create virtual dependency package so it can be deleted after use
RUN apk add gcc libffi-dev musl-dev postgresql-dev git

RUN pip install -q poetry

COPY pyproject.toml poetry.lock ./

RUN poetry export --without-hashes -f requirements.txt > ./requirements.txt

# As dmpy is hosted on git (outside of pip) we must be able to install it via git ...
# Annoyingly this is built with each step because the requirements file is passed between images
RUN pip install -q -r ./requirements.txt

COPY . /app/

ENV PYTHONPATH=/app

# NOTE: for now we are running a pipeline via cron to test infrastructure there
# would be no RUN/CMD as this image would be used in a compose file (airflow).
RUN echo '* * * * * cd /app/ && python ./data_transfer/main.py DRM kiel' > /etc/crontabs/root

# Set crond to foreground so it is always running
# and set log level to list when critical.
CMD ["crond", "-f", "-l", "2"]