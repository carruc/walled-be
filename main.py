import sys
import os

from fastapi import FastAPI
from api.endpoints import router as api_router
from api.websocket import router as websocket_router
from api.purchase_endpoints import router as purchase_router

app = FastAPI()

app.include_router(api_router, prefix="/api/v1")
app.include_router(websocket_router)
app.include_router(purchase_router, prefix="/api/v1")


@app.get("/")
def read_root():
    return {"Hello": "World"}

