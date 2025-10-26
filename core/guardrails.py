from pydantic import BaseModel
import logging
import asyncio
import httpx
from .config import RUNPOD_API_KEY, RUNPOD_SL_ID, RUNPOD_POLL_INTERVAL_S, RUNPOD_MAX_WAIT_S

logger = logging.getLogger("guardrails.prompt_injection")

async def check_guardrails(amount: float, currency: str, item: str, site: str) -> bool:
    # In a real scenario, we would load the guardrails from a database or a config file.
    # For now, we'll use a hardcoded example.


    if amount < 10.0 and "amazon" in site:
        print(f"Guardrail check approved: amount {amount} bought from amazon")
        return True

    if amount > 50.0:
        print(f"Guardrail check failed: amount {amount} exceeds max price 50.0 euros")
        return False

    # Placeholder for prompt injection check
    if "shopify" in site:
        print(f"Guardrail check failed: shopify is not allowed")
        return False

    return True


class PromptInjectionDetected(Exception):
    pass


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
        # Analyze final status JSON and raise on high-confidence injection
        result_json = status_json or {}

        try:
            """
            outputs = []
            out = result_json.get("output") or result_json.get("outputs") or result_json.get("result")
            if isinstance(out, list):
                outputs = out
            elif isinstance(out, dict):
                outputs = [out]

            def check_entry(entry: dict) -> tuple[bool, float]:
                # Direct label/score
                label = str(entry.get("label") or entry.get("classification") or entry.get("prediction") or "").upper()
                score = entry.get("score") or entry.get("confidence") or entry.get("probability")
                if label == "INJECTION" and isinstance(score, (int, float)):
                    return True, float(score)
                # Nested labels list
                labels = entry.get("labels") or entry.get("classes") or entry.get("categories")
                if isinstance(labels, list):
                    for item in labels:
                        if not isinstance(item, dict):
                            continue
                        l = str(item.get("label") or item.get("name") or "").upper()
                        s = item.get("score") or item.get("confidence") or item.get("probability")
                        if l == "INJECTION" and isinstance(s, (int, float)):
                            return True, float(s)
                return False, 0.0

            detected = False
            detected_score = 0.0
            for entry in outputs:
                if isinstance(entry, dict):
                    hit, sc = check_entry(entry)
                    if hit and sc > detected_score:
                        detected = True
                        detected_score = sc
            """
            output = result_json.get("output");
            print(f"[Guardrail PI] Output: {output}, label: {output['label']}, score: {output['score']}")
            if output['label'] == "INJECTION" and output['score'] > 0.7:
                print(f"[Guardrail PI] Prompt injection detected (score={output['score']:.2f})")
                raise PromptInjectionDetected(f"Prompt injection detected (score={output['score']:.2f})")
        except PromptInjectionDetected:
            # Re-raise our signal exception
            raise
        except Exception as e:
            # Parsing errors should not fail the guardrail call itself
            logger.warning("Error parsing guardrail output: %s", e)

        return result_json