import asyncio
import json
import sys
import time
from datetime import datetime
from playwright.async_api import async_playwright
from playwright_stealth import Stealth


async def search_ozon(query: str, sku: str) -> dict:
    async with async_playwright() as p:
        # Запускаем Chromium браузер
        browser = await p.chromium.launch(
            headless=False,  # False = видимый браузер (True = скрытый, но Озон блокирует)
            # proxy={"server": "socks5://127.0.0.1:10808"},  # весь трафик через Happ - раскомментировать если блок
            args=[
                "--disable-blink-features=AutomationControlled"
            ],  # скрываем признак автоматизации
        )
        # Создаём контекст = настройки "личности" браузера
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",  # говорим что мы обычный Chrome
            viewport={"width": 1920, "height": 1080},  # размер окна
            locale="ru-RU",  # язык
            timezone_id="Europe/Moscow",  # часовой пояс
        )

        # Открываем новую вкладку
        page = await context.new_page()

        # Патчим браузер чтобы скрыть признаки автоматизации
        # navigator.webdriver = главный сигнал что это бот
        await Stealth().apply_stealth_async(page)

        all_skus = []

        # Эта функция будет вызываться для КАЖДОГО ответа браузера
        async def on_response(response):
            url = response.url

            # Фильтр — нам нужен только API с товарами
            if "entrypoint-api.bx/page/json/v2" in url and response.status == 200:
                try:
                    # Парсим JSON ответ
                    data = await response.json()

                    # Перебираем все виджеты страницы
                    for key, value in data.get("widgetStates", {}).items():

                        # Нас интересует только виджет сетки товаров
                        if "tileGridDesktop" in key:

                            # value это строка содержащая JSON — парсим второй раз
                            widget_data = json.loads(value)

                            # items = список товаров
                            for item in widget_data.get("items", []):

                                # SKU товара лежит в поле "sku" (число)
                                item_sku = str(item.get("sku", ""))

                                # Добавляем в список если ещё нет
                                if item_sku and item_sku not in all_skus:
                                    all_skus.append(item_sku)
                except Exception:
                    pass  # если что-то пошло не так — просто пропускаем

        # Подписываемся на событие "получен ответ от сервера"
        page.on("response", on_response)

        # Открываем страницу поиска
        await page.goto(
            f"https://www.ozon.ru/search/?text={query}&sorting=score",
            wait_until="domcontentloaded",  # ждём загрузки DOM (не всех ресурсов)
        )

        # Ждём пока body появится и товары подгрузятся
        await page.wait_for_selector("body", timeout=10000)
        await asyncio.sleep(4)

        # Скроллим страницу вниз пока не наберём 100 товаров
        # Озон подгружает товары лениво — только когда скроллишь вниз
        max_attempts = 15
        attempt = 0
        while len(all_skus) < 100 and attempt < max_attempts:
            prev_count = len(all_skus)
            body = await page.query_selector("body")
            if not body:
                await asyncio.sleep(2)
                attempt += 1
                continue
            # Скроллим в самый низ страницы
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2.5)
            attempt += 1
            # Если новые товары не появились 3 раза подряд — выходим
            if len(all_skus) == prev_count and attempt > 3:
                break

        await asyncio.sleep(1)
        await browser.close()

    # Ищем наш SKU в списке — индекс + 1 = позиция (список с 0, позиции с 1)
    position = all_skus.index(sku) + 1 if sku in all_skus else None

    return {
        "query": query,
        "sku": sku,
        "position": position if position else "not_found",
        "page": 1,
        "total_checked": len(all_skus),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    }


async def main():
    # Часть 1 — принимаем аргументы командной строки
    if len(sys.argv) == 3:
        query = sys.argv[1]
        sku = sys.argv[2]
        result = await search_ozon(query, sku)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    # Часть 2 — режим устойчивости: 3 запуска с паузой 30 сек
    elif len(sys.argv) == 2 and sys.argv[1] == "--stability-test":
        test_cases = [
            ("термос", "1758986739"),
            ("наушники bluetooth", "1806278379"),
            ("рюкзак туристический", "890821097"),
        ]
        for run, (query, sku) in enumerate(test_cases, 1):
            print(f"\n{'='*40}")
            print(f"Запуск {run}/3  [{datetime.now().strftime('%H:%M:%S')}]")
            result = await search_ozon(query, sku)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            fname = f"run_{run}.json"
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            if run < 3:
                print(f"\nПауза 30 сек...")
                time.sleep(30)
        print(f"\n{'='*40}")
        print("Все 3 запуска завершены!")

    # Без аргументов — показываем подсказку
    else:
        print("Использование:")
        print('  python parser.py "термос" "1758986739"')
        print("  python parser.py --stability-test")


asyncio.run(main())
