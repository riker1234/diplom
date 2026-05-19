import sys, json, time
sys.stdout.reconfigure(encoding='utf-8')
import os
os.environ.setdefault("DATABASE_URL", open(".env").read().split("DATABASE_URL=")[1].split()[0])
from urllib.parse import quote
import app.parsers.ozon as oz

print("Инициализация...")
driver = oz._get_driver()
print(f"URL: {driver.current_url}")

# Дополнительный прогрев - подождём больше
print("Доп. ожидание 8 сек...")
time.sleep(8)

# Тестируем raw _browser_get
query = "клавиатура механическая"
api_url = (
    f"/api/entrypoint-api.bx/page/json/v2"
    f"?url=/search/?text={quote(query)}"
    f"&layout_container=categorySearchMegapagination&layout_page_index=1"
)
print(f"\nЗапрос: {api_url[:100]}")

data = oz._browser_get(api_url)
if data is None:
    print("_browser_get вернул None")
    # Проверим что именно вернул скрипт
    escaped = api_url.replace("'", "\\'")
    result = driver.execute_async_script(f"""
        var callback = arguments[arguments.length - 1];
        fetch('{escaped}')
            .then(r => {{
                var status = r.status;
                return r.text().then(t => callback({{status: status, body: t.substring(0, 500)}}))
            }})
            .catch(e => callback({{error: e.toString()}}))
    """)
    print(f"Raw result: {result}")
else:
    ws = data.get("widgetStates", {})
    products = oz._extract_products(ws)
    print(f"widgetStates: {len(ws)}, products: {len(products)}")
    if products:
        print(f"  Первый: {oz._get_name(products[0])} — {oz._get_price(products[0])}₽")

driver.quit()
