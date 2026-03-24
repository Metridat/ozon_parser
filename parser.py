# spy.py v2 — с антидетектом
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="ru-RU",
            timezone_id="Europe/Moscow",
        )

        # Главный трюк — убираем признак автоматизации
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
            window.chrome = {runtime: {}};
        """)

        page = await context.new_page()

        def on_response(response):
            url = response.url
            if "api" in url or "composer" in url or "search" in url:
                print(f"[RES] {response.status} {url[:120]}")

        page.on("response", on_response)

        print("Открываю Ozon...")
        await page.goto("https://www.ozon.ru/search/?text=термос",
                        wait_until="domcontentloaded")

        print("Жду 10 секунд...")
        await asyncio.sleep(10)

        # Скажи нам — что показал браузер
        title = await page.title()
        print(f"Заголовок: {title}")
        
        await browser.close()

asyncio.run(main())