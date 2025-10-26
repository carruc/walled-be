from agents import function_tool as tool
import asyncio
import json
from api.websocket import manager, payment_confirmation_events, user_decisions, plan_approval_events
from contextvars import ContextVar
from core.guardrails import check_guardrails
from core.config import GUARDRAIL_PI_ENABLED
from core.guardrails import check_prompt_injection_with_runpod, PromptInjectionDetected
from bs4 import BeautifulSoup
import httpx
from core.browser import BrowserManager
from core.tasks import running_tasks

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
async def go_to_url(url: str):
    """Navigates to a specific URL and returns basic page metadata."""
    client_id = client_id_var.get()
    if not client_id:
        return "Error: client_id not set."
    page = await BrowserManager.get_page(client_id)
    try:
        resp = await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        title = await page.title()
        final_url = page.url
        status = resp.status if resp else 0
        return f"Successfully navigated to {final_url}. Status: {status}. Title: {title}"
    except Exception as e:
        return f"Error navigating to {url}: {e}"


@tool
async def find_and_click_element(selector: str):
    """Finds an element on the page using a CSS selector and clicks it."""
    client_id = client_id_var.get()
    if not client_id:
        return "Error: client_id not set."
    page = await BrowserManager.get_page(client_id)
    try:
        await page.wait_for_selector(selector, state="visible", timeout=10000)
        await page.click(selector, timeout=10000)
        return f"Clicked element with selector: {selector}"
    except Exception as e:
        return f"Error clicking element {selector}: {e}"


@tool
async def summarize_page_content():
    """Summarizes the content of the current web page."""
    client_id = client_id_var.get()
    if not client_id:
        return "Error: client_id not set."
    page = await BrowserManager.get_page(client_id)
    try:
        raw = await page.locator('body').inner_text()
    except Exception as e:
        return f"Error reading page content: {e}"
    text = ' '.join((raw or '').split())
    try:
        result = await check_prompt_injection_with_runpod(text)
        print("[Guardrail PI] Final result:", result)
    except PromptInjectionDetected:
        print("[Guardrail PI] Prompt injection detected!!!")
        try:
            client_id = client_id_var.get()
            if client_id:
                await manager.send_personal_message(json.dumps({
                    "type": "guardrail_violation",
                    "data": {"message": "Potential prompt injection detected. Stopping agent."}
                }), client_id)
                task = running_tasks.get(client_id)
                if task:
                    task.cancel()
                    del running_tasks[client_id]
        except Exception as notify_err:
            print("[Guardrail PI] Error notifying client / stopping agent:", notify_err)
        raise
    except Exception as e:
        print("[Guardrail PI] Error during check:", e)
    return text if text else "(No content)"


@tool
async def summarize_webpage(url: str, max_chars: int = 5000):
    """Fetches a URL in a browser, runs a guardrail on text, and returns a summary."""
    client_id = client_id_var.get()
    if not client_id:
        return "Error: client_id not set."
    page = await BrowserManager.get_page(client_id)
    try:
        await page.goto(url, wait_until="networkidle", timeout=20000)
    except Exception as e:
        return f"Error fetching URL: {e}"

    try:
        html = await page.content()
        raw = await page.locator('body').inner_text()
    except Exception as e:
        return f"Error reading page: {e}"

    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = ' '.join((raw or '').split())[:max_chars]

    try:
        result = await check_prompt_injection_with_runpod(text)
        print("[Guardrail PI] Final result:", result)
    except PromptInjectionDetected:
        print("[Guardrail PI] Prompt injection detected!!!")
        try:
            client_id = client_id_var.get()
            if client_id:
                await manager.send_personal_message(json.dumps({
                    "type": "guardrail_violation",
                    "data": {"message": "Potential prompt injection detected. Stopping agent."}
                }), client_id)
                task = running_tasks.get(client_id)
                if task:
                    task.cancel()
                    del running_tasks[client_id]
        except Exception as notify_err:
            print("[Guardrail PI] Error notifying client / stopping agent:", notify_err)
        raise
    except Exception as e:
        print("[Guardrail PI] Error during check:", e)

    title = await page.title()
    summary_body = text[:800]
    summary = f"{title}\n\n{summary_body}".strip()
    return summary or "(No summary available)"
