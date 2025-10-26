import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Go to the Amazon login page
        await page.goto("https://www.amazon.de/gp/sign-in.html")

        print("Please log in to your Amazon account in the browser window.")
        print("Once you are logged in, you can close the browser.")

        # This will wait indefinitely until the page is closed, which you do after logging in
        await page.wait_for_event("close", timeout=0)

        # Save the authentication state to a file
        await context.storage_state(path="amazon_auth.json")
        print("Authentication state saved to amazon_auth.json")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
