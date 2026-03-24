import asyncio
import json
import random
import time
from datetime import datetime
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def search_ozon(query: str, sku: str) -> dict:
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

        all_skus = []

        async def on_response(response):
            url = response.url
            if "entrypoint-api.bx/page/json/v2" in url and response.status == 200:
                try:
                    data = await response.json()
                    for key, value in data.get("widgetStates", {}).items():
                        if "tileGridDesktop" in key:
                            widget_data = json.loads(value)
                            for item in widget_data.get("items", []):
                                item_sku = str(item.get("sku", ""))
                                if item_sku and item_sku not in all_skus:
                                    all_skus.append(item_sku)
                                    print(f"  SKU найден: {item_sku}")
                except Exception:
                    pass

        page.on("response", on_response)

        await page.goto(
            f"https://www.ozon.ru/search/?text={query}&sorting=score",
            wait_until="domcontentloaded"
        )

        for scroll_y in [600, 1200, 1800, 2400]:
            await page.evaluate(f"window.scrollTo(0, {scroll_y})")
            await asyncio.sleep(1.5)

        await asyncio.sleep(2)
        await browser.close()

    position = all_skus.index(sku) + 1 if sku in all_skus else None

    return {
        "query": query,
        "sku": sku,
        "position": position if position else "not_found",
        "page": 1,
        "total_checked": len(all_skus),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }


# async def main():
#     test_cases = [
#         ("термос",              "1758986739"),
#         ("наушники bluetooth",  "1288068946"),
#         ("рюкзак туристический","548925834"),
#     ]

#     results = []
#     for i, (query, sku) in enumerate(test_cases):
#         print(f"\n[{i+1}/3] Запрос: '{query}', SKU: {sku}")
#         result = await search_ozon(query, sku)
#         print(json.dumps(result, ensure_ascii=False, indent=2))
#         results.append(result)

#         if i < len(test_cases) - 1:
#             delay = random.uniform(28, 35)
#             print(f"[*] Пауза {delay:.0f} сек...")
#             time.sleep(delay)

#     with open("results.json", "w", encoding="utf-8") as f:
#         json.dump(results, f, ensure_ascii=False, indent=2)
#     print("\n[*] Готово! Результаты в results.json")


async def main():
    queries = ["наушники bluetooth", "рюкзак туристический"]
    for query in queries:
        print(f"\n=== {query} ===")
        await search_ozon(query, "0")

asyncio.run(main())
        