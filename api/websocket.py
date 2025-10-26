from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json

router = APIRouter()

payment_confirmation_events = {}
plan_approval_events = {}
user_decisions = {}


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[client_id] = websocket

    def disconnect(self, client_id: str):
        del self.active_connections[client_id]

    async def send_personal_message(self, message: str, client_id: str):
        await self.active_connections[client_id].send_text(message)


manager = ConnectionManager()


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(client_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            if message.get("type") == "payment_response":
                decision = message.get("data", {}).get("decision")
                if client_id in payment_confirmation_events:
                    user_decisions[client_id] = decision
                    payment_confirmation_events[client_id].set()
            elif message.get("type") == "plan_response":
                decision = message.get("data", {}).get("decision")
                if client_id in plan_approval_events:
                    user_decisions[client_id] = decision
                    plan_approval_events[client_id].set()
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except json.JSONDecodeError:
        await manager.send_personal_message("Invalid JSON format.", client_id)
