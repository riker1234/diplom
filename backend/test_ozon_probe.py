import sys, json, time
sys.stdout.reconfigure(encoding='utf-8')

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager

def make_driver():
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
    stealth(driver, languages=["ru-RU", "ru"], vendor="Google Inc.",
            platform="Win32", webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine", fix_hairline=True)
    return driver

driver = make_driver()
driver.set_script_timeout(30)

try:
    print("Загружаем ozon.ru...")
    driver.get("https://www.ozon.ru/")
    time.sleep(5)

    # ── 1. Поиск товаров ────────────────────────────────────────
    print("\n=== SEARCH ===")
    search_url = "/api/entrypoint-api.bx/page/json/v2?url=/search/?text=%D0%B8%D0%B3%D1%80%D0%BE%D0%B2%D0%B0%D1%8F+%D0%BC%D1%8B%D1%88%D1%8C&layout_container=categorySearchMegapagination&layout_page_index=1"
    result = driver.execute_async_script(f"""
        var callback = arguments[arguments.length - 1];
        fetch('{search_url}')
            .then(r => r.json())
            .then(data => callback(data))
            .catch(e => callback({{error: e.toString()}}))
    """)

    if not isinstance(result, dict) or "error" in result:
        print(f"Search error: {result}")
    else:
        print(f"Top-level keys: {list(result.keys())}")
        widget_states = result.get("widgetStates", {})
        print(f"widgetStates count: {len(widget_states)}")
        print(f"widgetStates keys (first 20): {list(widget_states.keys())[:20]}")

        found_items = []
        for key in widget_states:
            if any(x in key for x in ["searchResultsV2", "tileGrid", "searchResults"]):
                print(f"\nFound product widget key: {key}")
                try:
                    w = json.loads(widget_states[key]) if isinstance(widget_states[key], str) else widget_states[key]
                    items = w.get("items", [])
                    print(f"Items count: {len(items)}")
                    if items:
                        found_items = items
                        first = items[0]
                        print("\nFirst item keys:", list(first.keys()))
                        print("\nFirst item JSON:")
                        print(json.dumps(first, ensure_ascii=False, indent=2)[:3000])
                except Exception as e:
                    print(f"Parse error: {e}")
                break

        # ── 2. Характеристики товара ──────────────────────────────
        if found_items:
            first = found_items[0]
            # Найдем URL товара
            product_url = (
                first.get("urlForProduct") or
                first.get("action", {}).get("link", "") or
                first.get("link", "")
            )
            product_id = first.get("id") or first.get("sku")
            print(f"\n>>> product_id={product_id}, product_url={product_url}")

            if product_url:
                print(f"\n=== PRODUCT CHARS ({product_url}) ===")
                chars_url = f"/api/entrypoint-api.bx/page/json/v2?url={product_url}"
                result2 = driver.execute_async_script(f"""
                    var callback = arguments[arguments.length - 1];
                    fetch('{chars_url}')
                        .then(r => r.json())
                        .then(data => callback(data))
                        .catch(e => callback({{error: e.toString()}}))
                """)

                if not isinstance(result2, dict) or "error" in result2:
                    print(f"Chars error: {result2}")
                else:
                    ws2 = result2.get("widgetStates", {})
                    print(f"ALL widget keys ({len(ws2)}):")
                    for k in ws2.keys():
                        print(f"  {k}")
                    # Print ALL characteristic-related widgets
                    for key in ws2:
                        if "characteristic" in key.lower():
                            print(f"\n=== Widget: {key} ===")
                            try:
                                w = json.loads(ws2[key]) if isinstance(ws2[key], str) else ws2[key]
                                print(json.dumps(w, ensure_ascii=False, indent=2)[:8000])
                            except Exception as e:
                                print(f"Parse error: {e}")

finally:
    driver.quit()
    print("\nДрайвер закрыт")
