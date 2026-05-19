import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
os.environ.setdefault("DATABASE_URL", open(".env").read().split("DATABASE_URL=")[1].split()[0])

import app.parsers.ozon as oz

print("Инициализация драйвера...")
try:
    driver = oz._get_driver()
    print(f"OK, URL: {driver.current_url}")
except Exception as e:
    print(f"ОШИБКА драйвера: {e}")
    sys.exit(1)

print("\nПробуем _browser_get...")
data = oz._browser_get("/api/entrypoint-api.bx/page/json/v2?url=/search/?text=%D0%BA%D0%BB%D0%B0%D0%B2%D0%B8%D0%B0%D1%82%D1%83%D1%80%D0%B0&layout_container=categorySearchMegapagination&layout_page_index=1")
if data:
    ws = data.get("widgetStates", {})
    print(f"widgetStates keys: {len(ws)}")
    products = oz._extract_products(ws)
    print(f"products found: {len(products)}")
    if products:
        p = products[0]
        print(f"  name: {oz._get_name(p)}")
        print(f"  price: {oz._get_price(p)}")
        print(f"  brand: {oz._get_brand(p)}")
else:
    print("_browser_get вернул None")

driver.quit()
