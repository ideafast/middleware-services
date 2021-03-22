# IDEA-FAST WP3 Middleware Services

Currently developing scripts to facilitate _data transfer_ between sensor device manufactures and IDEA-FAST's internal data platform, and a separate _consumer_ API to provide updates on device wear and use.

## Installation

[Poetry](https://python-poetry.org/) is used for dependency management and
[pyenv](https://github.com/pyenv/pyenv) to manage python installations, so
please install both on your local machine. We use python 3.8 by default, so
please make sure this is installed via pyenv, e.g.

    pyenv install 3.8.0 && pyenv global 3.8.0

Once done, you can install dependencies for this project via:

    poetry install --no-dev

To setup a virtual environment with your local pyenv version run:

    poetry shell

## Setting up Environmental Files

Copy `.NAME.dev.env.example` file to `.NAME.dev.env` where `NAME` is the python package (consumer, data_transfer).
Then add relevant local/live values and credentials. You will need `.NAME.dev.env.example` if deploying

## Local Development

For development, install additional dependencies through:

    poetry install
    poetry run pre-commit install

When developing the consumer API run:

    poetry run consumer

When developing the data transfer jobs run where `DEVICE_TYPE` is the type of device (e.g., DRM, BTF, etc.) and `study_site` is one of the core study sites. View the [DAGs in data_transfer](./data_transfer/dags/) for more information:

    python data_transfer/main.py $DEVICE_TYPE $STUDY_SITE

### Running Tests, Type Checking, Linting and Code Formatting

[Nox](https://nox.thea.codes/) is used for automation and standardisation of tests, type hints, automatic code formatting, and linting. Any contribution needs to pass these tests before creating a Pull Request.

To run all these libraries:

    poetry run nox -r

Or individual checks by choosing one of the options from the list:

    poetry run nox -rs [tests, mypy, isort, lint, black]

### Developing with Docker

[Docker](https://www.docker.com/) is used to build images both for the consumer and data_transfer services. A [docker-compose file](./docker-compose.yml) configures the required services and image needed for local development. This can be run locally when developing if interacting with a service (e.g., consumer) to mirror deployment usage. To run the compose file you first need to create two docker networks:

    docker network create web
    docker network create database

[Semantic versioning](https://semver.org/) is used when core changes are merged
to master to enable continuous deployment. To build an image locally run the following
where `$VERSION` is your desired version and `$REPO` is the name of the image:

    poetry run build $VERSION $REPO
    # e.g., poetry run build 0.0.1 dtransfer

The compose file uses specified `.env` files and runs all services:

    poetry run compose

*Note:* for local development docker is primarily used to test changes prior to deploying live _or_ to interact with services in isolation.

### Deploying

[Docker Hub](https://hub.docker.com/u/ideafast) is used to store images. To push
to an image to a `$REPO` run  the following:

    poetry run publish $VERSION $REPO