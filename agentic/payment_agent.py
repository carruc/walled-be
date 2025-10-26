"""
Browser-based purchase automation using AI agents.
Integrates browser-use with OpenAI for automated Amazon checkout.
"""

from browser_use import Agent, Browser, BrowserConfig
from browser_use.llm import ChatOpenAI
from typing import Dict, Optional
import os
import asyncio
import logging
import re

logger = logging.getLogger(__name__)


class PurchaseAgent:
    """
    AI agent for executing Amazon purchases using saved credentials
    in a local BrowserOS profile.
    """

    def __init__(
        self,
        profile_path: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        headless: bool = True
    ):
        """
        Initialize purchase agent with BrowserOS profile and OpenAI LLM.
        
        Args:
            profile_path: Path to BrowserOS profile directory (default from env)
            openai_api_key: OpenAI API key (default from env)
            headless: Run browser in headless mode (True for production)
        """
        # Get profile path from env or parameter
        self.profile_path = profile_path or os.getenv(
            'BROWSEROS_PROFILE_PATH',
            '/Users/carruc/Library/Application Support/BrowserOS/walled-agent'
        )
        
        # Configure browser settings
        self.browser_config = BrowserConfig(
            headless=headless,
            disable_security=False,
            extra_chromium_args=[
                f'--user-data-dir={self.profile_path}',
                '--disable-blink-features=AutomationControlled',  # Anti-detection
                '--no-first-run',
                '--no-default-browser-check',
            ]
        )
        
        # Initialize OpenAI LLM via LangChain
        api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY in .env")
        
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",  # Optimal cost/performance for browser automation
            temperature=0.1,  # Low temperature for consistent, deterministic behavior
            api_key=api_key,
            timeout=60,  # Timeout for LLM API calls
        )
        
        logger.info(f"PurchaseAgent initialized with profile: {self.profile_path}")
    
    async def execute_purchase(
        self,
        product_url: str,
        approved: bool = False,
        max_actions: int = 30
    ) -> Dict:
        """
        Execute automated Amazon purchase using AI agent.
        
        Args:
            product_url: Clean Amazon product URL (e.g., https://amazon.com/dp/B08...)
            approved: Whether purchase has been approved by user/system
            max_actions: Maximum number of actions agent can take
            
        Returns:
            Dict with status, order_number (if successful), and metadata
        """
        if not approved:
            logger.warning(f"Purchase not approved for: {product_url}")
            return {
                "status": "rejected",
                "message": "Purchase not approved by user or system",
                "product_url": product_url
            }
        
        # Validate Amazon URL
        if not self._is_valid_amazon_url(product_url):
            logger.error(f"Invalid Amazon URL: {product_url}")
            return {
                "status": "error",
                "message": "Invalid Amazon URL provided",
                "product_url": product_url
            }
        
        logger.info(f"Starting purchase automation for: {product_url}")
        
        # Initialize browser with BrowserOS profile
        browser = Browser(config=self.browser_config)
        
        # Create AI agent task
        task = f"""
        Navigate to {product_url} on Amazon.
        
        First, verify that you are logged into Amazon by checking for account name.
        
        Then, add the product to your cart using the "Add to Cart" button.
        
        After adding to cart, proceed to checkout.
        
        Complete the purchase using the SAVED payment method and shipping address.
        Do NOT modify any payment or shipping information - use what's already saved.
        
        After successfully placing the order, extract the order number from the confirmation page.
        
        Return the order number and confirmation details.
        
        If at any point you encounter an error (out of stock, payment issue, etc.),
        report the error clearly.
        """
        
        try:
            # Create browser-use agent
            agent = Agent(
                task=task,
                llm=self.llm,
                browser=browser,
                max_actions_per_step=max_actions,
            )
            
            # Execute the agent (this runs the browser automation)
            logger.info("Agent executing purchase task...")
            result = await agent.run()
            
            logger.info(f"Agent completed task: {result.final_result()}")
            
            # Parse agent result to extract order info
            order_info = self._parse_agent_result(result)
            
            return {
                "status": "success",
                "message": "Purchase completed successfully",
                "product_url": product_url,
                "order_number": order_info.get("order_number", "Unknown"),
                "agent_result": result.final_result(),
                "actions_taken": len(result.history),
            }
            
        except Exception as e:
            logger.exception(f"Purchase automation failed: {e}")
            return {
                "status": "error",
                "message": f"Purchase automation failed: {str(e)}",
                "product_url": product_url,
                "error_type": type(e).__name__
            }
        
        finally:
            # Always close browser to free resources
            await browser.close()
            logger.info("Browser closed")
    
    def _is_valid_amazon_url(self, url: str) -> bool:
        """Validate that URL is from Amazon domain."""
        amazon_domains = ['amazon.com', 'amazon.co.uk', 'amazon.de', 'amazon.it']
        return any(domain in url.lower() for domain in amazon_domains)
    
    def _parse_agent_result(self, result) -> Dict:
        """
        Extract structured information from agent result.
        
        Args:
            result: Browser-use agent result object
            
        Returns:
            Dict with order_number and other extracted info
        """
        final_result = result.final_result()
        
        # Simple extraction - you can make this more sophisticated
        order_info = {
            "order_number": "Unknown",
            "raw_result": final_result
        }
        
        # Try to extract order number from result text
        # Amazon order numbers are typically like: 123-4567890-1234567
        order_match = re.search(r'\d{3}-\d{7}-\d{7}', final_result)
        if order_match:
            order_info["order_number"] = order_match.group(0)
        
        return order_info


# Singleton instance for reuse across requests
_purchase_agent_instance: Optional[PurchaseAgent] = None


def get_purchase_agent(headless: bool = True) -> PurchaseAgent:
    """
    Get or create PurchaseAgent singleton instance.
    
    Args:
        headless: Run browser in headless mode
        
    Returns:
        Shared PurchaseAgent instance
    """
    global _purchase_agent_instance
    
    if _purchase_agent_instance is None:
        _purchase_agent_instance = PurchaseAgent(headless=headless)
    
    return _purchase_agent_instance
