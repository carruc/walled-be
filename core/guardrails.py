from pydantic import BaseModel
import logging
import asyncio
import httpx
from .config import RUNPOD_API_KEY, RUNPOD_SL_ID, RUNPOD_POLL_INTERVAL_S, RUNPOD_MAX_WAIT_S


class Guardrails(BaseModel):
    max_price: float | None = None
    # Add other guardrails here


async def check_guardrails(amount: float, currency: str, item: str) -> bool:
    # In a real scenario, we would load the guardrails from a database or a config file.
    # For now, we'll use a hardcoded example.
    guardrails = Guardrails(max_price=100.0)

    if guardrails.max_price and amount > guardrails.max_price:
        print(f"Guardrail check failed: amount {amount} exceeds max price {guardrails.max_price}")
        return False

    # Placeholder for prompt injection check
    if "buy this now" in item.lower():
        print(f"Guardrail check failed: potential prompt injection detected for item: {item}")
        return False

    return True


logger = logging.getLogger("guardrails.prompt_injection")


async def check_prompt_injection_with_runpod(prompt: str) -> dict:
    """Call Runpod endpoint to check for prompt injection on the given prompt.

    Logs every request and response, polling until status is not IN_QUEUE/IN_PROGRESS.
    Returns the final status JSON (or an error/skipped payload).
    """
    print("[Guardrail PI] Checking prompt injection with Runpod for prompt:", prompt)
    if not RUNPOD_API_KEY or not RUNPOD_SL_ID:
        logger.warning("Runpod guardrail not configured; skipping.")
        return {"skipped": True}

    base = f"https://api.runpod.ai/v2/{RUNPOD_SL_ID}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
    }
    redacted_headers = {**headers, "Authorization": "Bearer ***REDACTED***"}
    payload = {"input": {"prompt": prompt}}

    async with httpx.AsyncClient() as client:
        logger.info("POST %s/run headers=%s json=%s", base, redacted_headers, payload)
        print("[Guardrail PI] Initial POST", {
            "url": f"{base}/run",
            "headers": redacted_headers,
            "json": payload
        })
        run = await client.post(f"{base}/run", headers=headers, json=payload)
        run.raise_for_status()
        run_json = run.json()
        logger.info("<- %s %s", run.status_code, run_json)
        req_id = run_json.get("id")
        if not req_id:
            return {"error": "no_id", "response": run_json}

        elapsed = 0.0
        status_json = None
        while True:
            logger.info("GET %s/status/%s headers=%s", base, req_id, redacted_headers)
            resp = await client.get(f"{base}/status/{req_id}", headers=headers)
            resp.raise_for_status()
            status_json = resp.json()
            logger.info("<- %s %s", resp.status_code, status_json)
            st = (status_json.get("status") or "").upper()
            if st not in ("IN_QUEUE", "IN_PROGRESS"):
                break
            await asyncio.sleep(RUNPOD_POLL_INTERVAL_S)
            elapsed += RUNPOD_POLL_INTERVAL_S
            if elapsed >= RUNPOD_MAX_WAIT_S:
                logger.warning("Guardrail poll timeout after %.1fs", elapsed)
                break
        return status_json or {}
