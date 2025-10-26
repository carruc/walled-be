"""
Browser-based purchase automation using AI agents.
Integrates browser-use with OpenAI for automated Amazon checkout.
"""

import asyncio
import os
from playwright.async_api import async_playwright
import logging

logger = logging.getLogger(__name__)

class PurchaseAgent:
    def __init__(self, auth_path="amazon_auth.json", headless=True):
        if not os.path.exists(auth_path):
            raise FileNotFoundError(f"Authentication file not found at {auth_path}. Please run create_auth.py first.")
        self.auth_path = auth_path
        self.headless = headless

    async def execute_purchase(self, product_url: str):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(storage_state=self.auth_path)
            page = await context.new_page()

            try:
                logger.info(f"Navigating to product page: {product_url}")
                await page.goto(product_url, wait_until="domcontentloaded")

                # Verify you are logged in by checking for an element that only appears when logged in
                try:
                    await page.wait_for_selector("#nav-link-accountList-nav-line-1", timeout=5000)
                    logger.info("Successfully verified login.")
                except Exception:
                    logger.error("Failed to verify login. The authentication state might be invalid.")
                    return {"status": "error", "message": "Failed to verify login.", "product_url": product_url}
                
                # --- Add to Cart ---
                add_to_cart_button = page.locator("#add-to-cart-button")
                if await add_to_cart_button.is_visible():
                    await add_to_cart_button.click()
                    logger.info("Product added to cart.")
                else:
                    logger.error("Could not find the 'Add to Cart' button.")
                    return {"status": "error", "message": "Could not find 'Add to Cart' button.", "product_url": product_url}

                # --- Proceed to Checkout ---
                # This selector may need updating depending on Amazon's A/B testing
                checkout_button = page.locator("#sc-buy-box-ptc-button, #hlb-ptc-btn-native")
                await checkout_button.click()
                logger.info("Proceeding to checkout.")

                # --- Place Order ---
                logger.info("Attempting to place the order...")
                # The ID "placeOrder" is not unique; we take the first visible one.
                place_order_button = page.locator("#placeOrder").first
                await place_order_button.click()

                # Wait for the confirmation page to load
                await page.wait_for_url("**/gp/buy/thankyou/**", timeout=30000)
                logger.info("Successfully placed the order and landed on confirmation page.")

                # This is a placeholder; extracting the order number would require
                # inspecting the confirmation page and finding the correct selector.
                order_number = "Unavailable"

                return {
                    "status": "success",
                    "message": "Purchase completed successfully.",
                    "product_url": product_url,
                    "order_number": order_number
                }

            except Exception as e:
                logger.exception(f"An error occurred during the purchase process: {e}")
                return {"status": "error", "message": str(e), "product_url": product_url}
            finally:
                await browser.close()


# Singleton instance for reuse across requests
_purchase_agent_instance: PurchaseAgent = None

def get_purchase_agent(headless: bool = True) -> PurchaseAgent:
    """
    Get or create PurchaseAgent singleton instance.
    """
    global _purchase_agent_instance
    
    if _purchase_agent_instance is None:
        _purchase_agent_instance = PurchaseAgent(headless=headless)
    
    return _purchase_agent_instance
