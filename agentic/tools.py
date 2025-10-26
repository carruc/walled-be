from agents import function_tool as tool
import asyncio
import json
from api.websocket import manager, payment_confirmation_events, user_decisions

# This is a hack to get the client_id to the tool.
_client_id = None


def set_client_id(client_id: str):
    global _client_id
    _client_id = client_id


@tool
async def request_payment_confirmation(amount: float, currency: str, item: str):
    """
    Requests user confirmation for a payment.
    This tool will pause execution until the user responds.
    """
    global _client_id
    if not _client_id:
        return "Error: client_id not set."

    client_id = _client_id
    event = asyncio.Event()
    payment_confirmation_events[client_id] = event
    
    payload = {
        "type": "payment_request",
        "data": {
            "amount": amount,
            "currency": currency,
            "item": item,
        }
    }
    await manager.send_personal_message(json.dumps(payload), client_id)

    await event.wait()

    decision = user_decisions.get(client_id, "denied")
    del payment_confirmation_events[client_id]
    if client_id in user_decisions:
        del user_decisions[client_id]

    if decision == "approved":
        return "Payment approved by user."
    else:
        return "Payment denied by user."


@tool
def go_to_url(url: str):
    """Navigates to a specific URL."""
    # This is a placeholder. In a real scenario, this would
    # use a browser automation library like Selenium or Playwright.
    print(f"Navigating to {url}")
    return f"Successfully navigated to {url}"


@tool
def find_and_click_element(selector: str):
    """Finds an element on the page using a CSS selector and clicks it."""
    # Placeholder
    print(f"Finding and clicking element with selector: {selector}")
    return f"Clicked element with selector: {selector}"


@tool
def summarize_page_content():
    """Summarizes the content of the current web page."""
    # Placeholder
    return "This is a summary of the page content."
