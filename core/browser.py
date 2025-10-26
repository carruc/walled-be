import asyncio
from typing import Dict, Tuple
from playwright.async_api import async_playwright, Browser, BrowserContext, Page


class BrowserManager:
    _playwright = None
    _browser: Browser | None = None
    _contexts: Dict[str, Tuple[BrowserContext, Page]] = {}

    @classmethod
    async def get_page(cls, client_id: str) -> Page:
        if cls._playwright is None:
            cls._playwright = await async_playwright().start()
            cls._browser = await cls._playwright.chromium.launch(headless=True, args=["--no-sandbox"])  # type: ignore
        if client_id not in cls._contexts:
            assert cls._browser is not None
            context = await cls._browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
                locale="en-US",
            )
            page = await context.new_page()
            cls._contexts[client_id] = (context, page)
        return cls._contexts[client_id][1]

    @classmethod
    async def close_page(cls, client_id: str) -> None:
        pair = cls._contexts.pop(client_id, None)
        if pair:
            context, page = pair
            try:
                await page.close()
            finally:
                await context.close()

    @classmethod
    async def shutdown(cls) -> None:
        for client_id in list(cls._contexts.keys()):
            await cls.close_page(client_id)
        if cls._browser:
            await cls._browser.close()
            cls._browser = None
        if cls._playwright:
            await cls._playwright.stop()
            cls._playwright = None


