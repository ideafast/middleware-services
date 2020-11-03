import uvicorn


if __name__ == '__main__':
    uvicorn.run("data_transfer.main:data_transfer", host="0.0.0.0", port=8001, reload=True)
