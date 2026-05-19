"""
Проверяем, продаёт ли DNS-shop.ru товары через маркетплейс Ozon.
Ищем товары с фильтром по продавцу "DNS" или "ДНС".
"""
import sys, json, re, time
sys.stdout.reconfigure(encoding='utf-8')
import os
os.environ['DATABASE_URL'] = open('.env').read().split('DATABASE_URL=')[1].split()[0]

from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options,
)
from selenium_stealth import stealth
stealth(driver, languages=["ru-RU", "ru"], vendor="Google Inc.",
        platform="Win32", webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine", fix_hairline=True)
driver.set_script_timeout(30)

print("Прогрев браузера...")
driver.get("https://www.ozon.ru/")
time.sleep(10)
print(f"Ozon title: {driver.title[:50]}")

def browser_get(url):
    escaped = url.replace("'", "\\'")
    return driver.execute_async_script(f"""
        var cb = arguments[arguments.length - 1];
        fetch('{escaped}')
            .then(r => r.json())
            .then(d => cb(d))
            .catch(e => cb({{error: e.toString()}}))
    """)

# Шаг 1: Ищем "DNS" как продавца через поиск продавцов
print("\n=== Шаг 1: Поиск продавца DNS/ДНС на Ozon ===")
seller_search_url = "/api/entrypoint-api.bx/page/json/v2?url=/seller/"
result = browser_get(seller_search_url)
if result and "error" not in result:
    print("Страница /seller/ получена")
    ws = result.get("widgetStates", {})
    print(f"Widget keys sample: {list(ws.keys())[:5]}")
else:
    print(f"Ошибка: {result}")

# Шаг 2: Поиск "игровая мышь" с продавцом dns
print("\n=== Шаг 2: Поиск мышей от продавца DNS ===")
# Попробуем найти через текстовый поиск
search_queries = [
    "/api/entrypoint-api.bx/page/json/v2?url=/search/?text=%D0%B8%D0%B3%D1%80%D0%BE%D0%B2%D0%B0%D1%8F+%D0%BC%D1%8B%D1%88%D1%8C+dns&layout_container=categorySearchMegapagination&layout_page_index=1",
]

for api_url in search_queries:
    result = browser_get(api_url)
    if result and "error" not in result:
        ws = result.get("widgetStates", {})
        for key, value in ws.items():
            if any(x in key for x in ("searchResultsV2", "tileGrid")):
                try:
                    data = json.loads(value)
                    items = data.get("items", [])
                    if items:
                        print(f"Найдено {len(items)} товаров в виджете {key[:50]}")
                        for item in items[:3]:
                            # ищем продавца
                            seller_info = None
                            for state in item.get("mainState", []):
                                if "seller" in str(state).lower() or "магазин" in str(state).lower():
                                    seller_info = state
                            print(f"  - ID={item.get('id')}, states: {[s.get('type') for s in item.get('mainState', [])]}")
                        break
                except Exception as e:
                    print(f"Ошибка парсинга: {e}")

# Шаг 3: Ищем напрямую страницу DNS на Ozon как магазина
print("\n=== Шаг 3: Прямой поиск магазина DNS на Ozon ===")
# Пробуем разные возможные seller ID
for search_q in ["DNS shop", "ДНС магазин мышь"]:
    api_url = f"/api/entrypoint-api.bx/page/json/v2?url=/search/?text={quote(search_q)}&layout_container=categorySearchMegapagination&layout_page_index=1"
    result = browser_get(api_url)
    if result and "error" not in result:
        ws = result.get("widgetStates", {})
        for key, value in ws.items():
            if any(x in key for x in ("searchResultsV2", "tileGrid")):
                try:
                    data = json.loads(value)
                    items = data.get("items", [])
                    if items:
                        print(f"'{search_q}': {len(items)} товаров")
                        first = items[0]
                        print(f"  Первый: id={first.get('id')}")
                        print(f"  mainState types: {[s.get('type') for s in first.get('mainState', [])]}")
                        # Смотрим полный первый элемент
                        print(f"  Полный дамп (500 символов): {json.dumps(first, ensure_ascii=False)[:500]}")
                except Exception as e:
                    print(f"  Ошибка: {e}")
    time.sleep(1)

# Шаг 4: Ищем конкретную мышь Logitech и смотрим есть ли продавец DNS
print("\n=== Шаг 4: Logitech G502 — ищем варианты продавцов ===")
api_url = f"/api/entrypoint-api.bx/page/json/v2?url=/search/?text={quote('logitech g502 мышь')}&layout_container=categorySearchMegapagination&layout_page_index=1"
result = browser_get(api_url)
if result and "error" not in result:
    ws = result.get("widgetStates", {})
    for key, value in ws.items():
        if any(x in key for x in ("searchResultsV2", "tileGrid")):
            try:
                data = json.loads(value)
                items = data.get("items", [])
                print(f"Logitech G502: {len(items)} результатов")
                for item in items[:5]:
                    pid = item.get("id")
                    # Ищем информацию о продавце в любом поле
                    full_str = json.dumps(item, ensure_ascii=False)
                    seller_mentions = []
                    for kw in ["seller", "продавец", "магазин", "ДНС", "DNS"]:
                        if kw.lower() in full_str.lower():
                            seller_mentions.append(kw)
                    print(f"  id={pid}, seller_kw={seller_mentions}, len={len(full_str)}")
            except Exception as e:
                print(f"Ошибка: {e}")

driver.quit()
print("\nГотово.")
