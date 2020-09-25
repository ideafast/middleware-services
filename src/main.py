import json
from fastapi import FastAPI


app = FastAPI()


@app.get('/devices')
async def devices():
    devices_file = open('devices.json')
    devices_data = json.load(devices_file)
    devices_file.close()
    return devices_data


@app.get('/devices/{device_id}/metrics')
async def metrics(device_id: str):
    metrics_file = open('metrics.json')
    metrics_data = json.load(metrics_file)
    metrics_file.close()
    return metrics_data


@app.get('/devices/{device_id}/status')
async def status(device_id: str):
    status_file = open('status.json')
    status_data = json.load(status_file)
    status_file.close()
    return status_data


@app.get('/verify')
async def verify():
    verification_file = open('verification.json')
    verification_data = json.load(verification_file)
    verification_file.close()
    return verification_data
