# IDEA-FAST WP3 Middleware Services

Currently developing scripts to facilitate data transfer between sensor device manufactures and IDEA-FAST's internal data platform, and a separate API to provide updates on device wear and use.

## Installation

[Poetry](https://python-poetry.org/) is used for dependency management and
[pyenv](https://github.com/pyenv/pyenv) to manage python installations, so
please install both on your local machine. We use python 3.8 by default, so
please make sure this is installed via pyenv, e.g.

    pyenv install 3.8.0 && pyenv global 3.8.0

Once done, you can install dependencies for this project via:

    poetry install

To setup a virtual environment with your local pyenv version run:

    poetry shell

## Setting up .env

Copy `.NAME.env.example` file to `.NAME.env` where `NAME` is the python package (consumer, data_transfer).
Then add relevant local/live values and credentials.

## Local Development

When developing the consumer API run:

    poetry run start

When developing the data transfer jobs run:

    poetry run transfer

### Deploying

To deploy the middleware we use Docker based on one image:

    docker build -t middleware .

The compose file contains all environmental variables and runs all services:

    docker-compose up -d

## Documentation

Interactive documentation is available in **Swagger** ([/docs](http://127.0.0.1:8000/docs)) and **ReDoc** ([/redoc](http://127.0.0.1:8000/redoc)).
