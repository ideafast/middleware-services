FROM python:3.8-alpine3.10 as base

# Saves having to add --no-cache-dir to pip installs
ENV PIP_NO_CACHE_DIR=1
# Causes error on pip
ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1

FROM base as builder

# Temporarily install dependencies to build/install poetry
# Create virtual dependency package so it can be deleted after use
RUN apk add --quiet --no-cache --virtual .build-deps gcc libffi-dev musl-dev postgresql-dev \
    && pip install -q poetry \
    && apk del .build-deps

COPY pyproject.toml poetry.lock ./

# Convert to requirements so we
RUN poetry export --without-hashes -f requirements.txt > /tmp/requirements.txt

FROM base as final

COPY --from=builder /tmp/requirements.txt /app/

# As dmpy is hosted on git (outside of pip) we must be able to install it via git ...
# Annoyingly this is built with each step because the requirements file is passed between images
RUN apk add --quiet --no-cache --virtual .deps gcc libffi-dev musl-dev postgresql-dev git \
    && pip install -q -r /app/requirements.txt \
    && apk del .deps

COPY . /app/

ENV PYTHONPATH=/app
WORKDIR /app

# NOTE: for now we are running a pipeline via cron to test infrastructure there
# would be no RUN/CMD as this image would be used in a compose file (airflow).
#
# NOTE: below is commented - image will need to be ran manually unless uncommented
# RUN echo '0 0 */3 * * python /app/data_transfer/main.py DRM kiel' > /etc/crontabs/root

# Set crond to foreground so it is always running
# and set log level to list when critical.
CMD ["crond", "-f", "-l", "2"]