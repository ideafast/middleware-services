## To install

1. `python3 -m pip install --user virtualenv`
1. `python3 -m venv env`
1. `source env/bin/activate`
1. `pip install fastapi[all]`
1. `uvicorn main:app --reload`

## Documentation

Visit `http://127.0.0.1:8000/docs#/` to see Swagger documentation
Visit `http://127.0.0.1:8000/redoc` to see ReDoc documentation
