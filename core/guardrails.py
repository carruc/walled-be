

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
