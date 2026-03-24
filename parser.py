import asyncio
import json
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            proxy={"server": "socks5://127.0.0.1:10808"},
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="ru-RU",
            timezone_id="Europe/Moscow",
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        async def on_response(response):
            url = response.url
            if "entrypoint-api.bx/page/json/v2" in url and "category" in url:
                try:
                    data = await response.json()
                    with open("ozon_response.json", "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    print(f"[ПОЙМАЛИ] Сохранили в ozon_response.json")
                    print(f"[КЛЮЧИ] {list(data.keys())}")
                except Exception as e:
                    print(f"[ОШИБКА] {e}")

        page.on("response", on_response)

        print("Открываю Ozon...")
        await page.goto(
            "https://www.ozon.ru/search/?text=термос",
            wait_until="domcontentloaded"
        )
        await asyncio.sleep(10)
        await browser.close()

asyncio.run(main())