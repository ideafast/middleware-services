from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv, find_dotenv
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import os
import requests


router = APIRouter()
load_dotenv(find_dotenv('.dtransfer.env'))
base_url = os.getenv("DMP_BASE_URL")
username = os.getenv("DMP_USERNAME")
password = os.getenv("DMP_PASSWORD")
totp = os.getenv("DMP_TOTP")


sample_transport = RequestsHTTPTransport(
    url=f"{base_url}graphql",
    use_json=True,
    headers={
        "Content-type": "application/json",
    }
)
client = Client(
    transport=sample_transport,
    fetch_schema_from_transport=True,
)


@router.get('/studies')
async def studies():
    query = gql('''
        fragment ALL_FOR_USER on User {
            id
            username
            type
            firstname
            lastname
            email
            organisation
            description
            access {
                id
                projects {
                    id
                    name
                    studyId
                }
                studies {
                    id
                    name
                }
            },
            createdAt,
            expiredAt
        }
        
        mutation login($username: String!, $password: String!, $totp: String!) {
          login(username: $username, password: $password, totp: $totp) {
              ...ALL_FOR_USER
          }
        }
    ''')
    params = {
        "username": username,
        "password": password,
        "totp": totp,
    }
    result = client.execute(query, params)
    login_response = requests.get(
        f"{base_url}graphql")
    if 400 <= login_response.status_code < 500:
        raise HTTPException(
            status_code=login_response.status_code,
            detail="General Error")
    return 'STUDIES'


def run_job():
    print('RUNNING DATA MANAGEMENT PLATFORM JOB')
