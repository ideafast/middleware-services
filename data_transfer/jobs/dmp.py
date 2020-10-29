from fastapi import APIRouter, HTTPException
import os
import requests


router = APIRouter()
base_url = os.getenv("DMP_BASE_URL")
username = os.getenv("DMP_USERNAME")
password = os.getenv("DMP_PASSWORD")
totp = os.getenv("DMP_TOTP")


@router.get('/studies')
async def studies():
    login_response = requests.get(
        f"{base_url}graphql")
    if 400 <= login_response.status_code < 500:
        raise HTTPException(
            status_code=login_response.status_code,
            detail="General Error")
    return 'STUDIES'


def run_job():
    print('RUNNING DATA MANAGEMENT PLATFORM JOB')
