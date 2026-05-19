"""
Проверяем seller API Ozon — ищем DNS или магазин ДНС как продавца.
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

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
stealth(driver, languages=["ru-RU", "ru"], vendor="Google Inc.",
        platform="Win32", webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine", fix_hairline=True)
driver.set_script_timeout(30)

print("Прогрев...")
driver.get("https://www.ozon.ru/")
time.sleep(10)

def browser_get(url):
    escaped = url.replace("'", "\\'")
    return driver.execute_async_script(f"""
        var cb = arguments[arguments.length - 1];
        fetch('{escaped}')
            .then(r => r.json())
            .then(d => cb(d))
            .catch(e => cb({{error: e.toString()}}))
    """)

# 1. Ищем seller через поиск продавцов
print("\n=== Поиск продавца 'DNS' через API ===")
for seller_name in ["DNS", "ДНС", "dns-shop"]:
    url = f"/api/entrypoint-api.bx/page/json/v2?url=/seller/?text={quote(seller_name)}"
    r = browser_get(url)
    if r and "error" not in r:
        ws = r.get("widgetStates", {})
        sellers_found = []
        for key, val in ws.items():
            if "seller" in key.lower() or "brand" in key.lower():
                try:
                    d = json.loads(val) if isinstance(val, str) else val
                    sellers_found.append((key[:40], str(d)[:200]))
                except:
                    pass
        print(f"'{seller_name}': {len(sellers_found)} seller widgets")
        for k, v in sellers_found[:3]:
            print(f"  {k}: {v[:150]}")
    time.sleep(1)

# 2. Смотрим товар с seller keyword
print("\n=== Logitech G502 — товар с seller info ===")
url = "/api/entrypoint-api.bx/page/json/v2?url=/product/logitech-g502-hero-gaming-189226603/features/"
r = browser_get(url)
if r and "error" not in r:
    ws = r.get("widgetStates", {})
    for key, val in ws.items():
        if "seller" in key.lower():
            try:
                d = json.loads(val) if isinstance(val, str) else val
                print(f"KEY: {key}")
                print(f"DATA: {json.dumps(d, ensure_ascii=False)[:400]}")
            except:
                pass

# 3. Страница конкретного продукта — ищем seller в widgetStates
print("\n=== Product page seller info ===")
url = "/api/entrypoint-api.bx/page/json/v2?url=/product/logitech-g502-hero-gaming-189226603/"
r = browser_get(url)
if r and "error" not in r:
    ws = r.get("widgetStates", {})
    for key, val in ws.items():
        key_lower = key.lower()
        if any(x in key_lower for x in ("seller", "merchant", "shop", "store", "магазин")):
            try:
                d = json.loads(val) if isinstance(val, str) else val
                print(f"\nKEY: {key[:60]}")
                print(f"DATA: {json.dumps(d, ensure_ascii=False)[:400]}")
            except:
                print(f"KEY: {key[:60]} (raw): {str(val)[:200]}")

# 4. Ищем через поиск с фильтром seller
print("\n=== Поиск с merchant/seller фильтром в URL ===")
# Попробуем известные seller ID DNS (если найдём)
for test_url in [
    "/api/entrypoint-api.bx/page/json/v2?url=/brand/dns/?layout_container=categorySearchMegapagination",
    "/api/entrypoint-api.bx/page/json/v2?url=/search/?text=dns+shop+мышь+игровая&seller=dns",
]:
    r = browser_get(test_url)
    if r and "error" not in r:
        ws = r.get("widgetStates", {})
        total_items = 0
        for key, val in ws.items():
            if any(x in key for x in ("tileGrid", "searchResults")):
                try:
                    d = json.loads(val)
                    items = d.get("items", [])
                    total_items += len(items)
                except:
                    pass
        print(f"URL: {test_url[-60:]!r} → {total_items} items")
    time.sleep(0.5)

driver.quit()
print("\nГотово.")
