# IDEA-FAST WP3 Middleware Services

Currently developing scripts to facilitate data transfer between sensor device manufactures and IDA-FAST's internal data platform, and a separate API to provide updates on device wear and use.

## Installation

[Poetry](https://python-poetry.org/) is used for dependency management and
[pyenv](https://github.com/pyenv/pyenv) to manage python installations, so
please install both on your local machine. Once done, you can install dependencies for this project via:

    poetry install

To setup a virtual environment with your local pyenv version run:

    poetry shell

## Local Development

    poetry run start

## Documentation

Interactive documentation is available at:

- Swagger: [http://127.0.0.1:8000/docs#](http://127.0.0.1:8000/docs#)
- ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
