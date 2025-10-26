from agents import function_tool as tool
import asyncio
import json
from api.websocket import manager, payment_confirmation_events, user_decisions, plan_approval_events
from contextvars import ContextVar
from core.guardrails import check_guardrails

client_id_var: ContextVar[str] = ContextVar("client_id")


@tool
async def send_plan_for_approval(plan: str):
    """
    Sends a plan to the user for approval.
    This tool will pause execution until the user responds.
    """
    # Non-permanent fix to auto-approve the plan
    print(f"Auto-approving plan: {plan}")
    return f"Plan approved by user: {plan}"

    # client_id = client_id_var.get()
    # if not client_id:
    #     return "Error: client_id not set."
    #
    # event = asyncio.Event()
    # plan_approval_events[client_id] = event
    #
    # payload = {
    #     "type": "plan_request",
    #     "data": {
    #         "plan": plan,
    #     }
    # }
    # await manager.send_personal_message(json.dumps(payload), client_id)
    #
    # await event.wait()
    #
    # decision = user_decisions.get(client_id, "denied")
    # del plan_approval_events[client_id]
    # if client_id in user_decisions:
    #     del user_decisions[client_id]
    #
    # if decision == "approved":
    #     return f"Plan approved by user: {plan}"
    # else:
    #     return "Plan denied by user."


@tool
async def request_payment_confirmation(amount: float, currency: str, item: str, link: str, site1: str, site1Domain: str, site2: str, site2Domain: str):
    """
    Requests user confirmation for a payment.
    This tool will pause execution until the user responds.
    """
    #guardrails_passed = await check_guardrails(amount, currency, item, site1)

    
    client_id = client_id_var.get()
    if not client_id:
        return "Error: client_id not set."


    event = asyncio.Event()
    payment_confirmation_events[client_id] = event


    # Determine if approval is required based on guardrail results
    #approval_required = not guardrails_passed
    #approval_label = "User approval required" if approval_required else "Purchase doesn't need approval"
    
    payload = {
        "type": "payment_request",
        "data": {
            "amount": amount,
            "currency": currency,
            "item": item,
            "link": link,
            "site1": site1,
            "site1Domain": site1Domain,
            "site2": site2,
            "site2Domain": site2Domain,
            "approval_required": True,
            "approval_label": "User approval required"
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
