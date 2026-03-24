import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://www.ozon.ru/search/?text=термос")
        await page.wait_for_timeout(5000)
        print("Заголовок страницы:", await page.title())
        await browser.close()

asyncio.run(main())