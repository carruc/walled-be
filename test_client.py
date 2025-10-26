import asyncio
import httpx
import websockets
import json
import uuid
import argparse

async def run_test(query: str):
    """
    A simple client to test the shopping agent functionality.
    """
    client_id = str(uuid.uuid4())
    ws_url = f"ws://localhost:8000/ws/{client_id}"
    api_url = "http://localhost:8000/api/v1/shop"

    try:
        async with websockets.connect(ws_url) as websocket:
            print(f"WebSocket connection established with client_id: {client_id}")

            # 1. Start the agent via HTTP request
            async with httpx.AsyncClient() as client:
                print(f"Sending shopping request for: '{query}'")
                response = await client.post(api_url, json={"query": query, "client_id": client_id})
                if response.status_code == 200:
                    print("Agent started successfully.")
                else:
                    print(f"Failed to start agent. Status: {response.status_code}, Response: {response.text}")
                    return

            # 2. Listen for messages and respond
            while True:
                message_str = await websocket.recv()
                message = json.loads(message_str)
                print(f"\n<-- Received message from server: {message}")

                if message.get("type") == "plan_request":
                    plan = message.get("data", {}).get("plan")
                    print(f"  - Received plan:\n{plan}")
                    # Automatically approve the plan
                    response = {
                        "type": "plan_response",
                        "data": {"decision": "approved"}
                    }
                    await websocket.send(json.dumps(response))
                    print(f"--> Sent plan approval.")

                elif message.get("type") == "payment_request":
                    payment_data = message.get("data", {})
                    print(f"  - Received payment request: {payment_data}")
                    # Automatically approve the payment
                    response = {
                        "type": "payment_response",
                        "data": {"decision": "approved"}
                    }
                    await websocket.send(json.dumps(response))
                    print(f"--> Sent payment approval.")
                    # We can exit after the first payment request for a simple test.
                    break

    except websockets.exceptions.ConnectionClosed as e:
        print(f"WebSocket connection closed: {e}")
    except ConnectionRefusedError:
        print("Connection refused. Is the server running on http://localhost:8000?")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test client for the shopping agent.")
    parser.add_argument(
        "query",
        type=str,
        help="The shopping query to send to the agent.",
        default="Find me the best laptop under $50.",
        nargs='?'
    )
    args = parser.parse_args()
    asyncio.run(run_test(args.query))
