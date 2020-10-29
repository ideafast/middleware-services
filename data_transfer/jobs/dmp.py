from fastapi import APIRouter, HTTPException
import os
import requests


router = APIRouter()
base_url = os.getenv("DMP_BASE_URL")


@router.get('/studies')
async def studies():
    return 'STUDIES'


def run_job():
    print('RUNNING DATA MANAGEMENT PLATFORM JOB')
