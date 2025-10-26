from fastapi import APIRouter
from pydantic import BaseModel
import asyncio
from agentic.shopping_agent import create_shopping_agent, run_agent
from api.websocket import manager
from core.tasks import running_tasks

router = APIRouter()


class ShopRequest(BaseModel):
    query: str
    client_id: str


@router.post("/shop")
async def shop(request: ShopRequest):
    if request.client_id in running_tasks:
        return {"status": "error", "message": "Agent already running for this client"}
    agent = create_shopping_agent()
    task = asyncio.create_task(run_agent(agent, request.query, request.client_id))
    running_tasks[request.client_id] = task
    return {"status": "ok", "message": "Agent started"}


class StopRequest(BaseModel):
    client_id: str


@router.post("/stop")
async def stop_agent(request: StopRequest):
    task = running_tasks.get(request.client_id)
    if not task:
        return {"status": "error", "message": "Agent not found"}

    task.cancel()
    del running_tasks[request.client_id]
    return {"status": "ok", "message": "Agent stopped"}
