from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from agents.shopping_agent import create_shopping_agent, run_agent
from api.websocket import manager

router = APIRouter()
agent = create_shopping_agent()


class ShopRequest(BaseModel):
    query: str
    client_id: str


@router.post("/shop")
async def shop(request: ShopRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(run_agent, agent, request.query, request.client_id)
    return {"status": "ok", "message": "Agent started"}
