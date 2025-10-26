from pydantic import BaseModel


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
