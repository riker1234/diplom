import time
import json
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

stealth(
    driver,
    languages=["ru-RU", "ru"],
    vendor="Google Inc.",
    platform="Win32",
    webgl_vendor="Intel Inc.",
    renderer="Intel Iris OpenGL Engine",
    fix_hairline=True,
)

print("Opening WB...")
driver.get("https://www.wildberries.ru/")
time.sleep(5)
print("Title:", driver.title)

# Вызываем поисковый API прямо из браузера — куки уже есть
result = driver.execute_async_script("""
    var callback = arguments[arguments.length - 1];
    fetch('https://www.wildberries.ru/__internal/u-search/exactmatch/ru/common/v18/search?ab_testing=false&appType=1&curr=rub&dest=-1257786&query=%D0%B8%D0%B3%D1%80%D0%BE%D0%B2%D0%B0%D1%8F+%D0%BC%D1%8B%D1%88%D1%8C&resultset=catalog&sort=popular&spp=30&suppressSpellcheck=false')
        .then(r => r.json())
        .then(data => callback(data))
        .catch(e => callback({error: e.toString()}))
""")

print("Keys:", list(result.keys()) if isinstance(result, dict) else type(result))
if "error" in result:
    print("Error:", result["error"])
else:
    products = result.get("products", [])
    print("Products found:", len(products))
    if products:
        p = products[0]
        pid = p.get("id")
        print("Name:", p.get("name"), "| ID:", pid)

        # Проверяем detail API
        detail = driver.execute_async_script(f"""
            var callback = arguments[arguments.length - 1];
            fetch('https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&nm={pid}')
                .then(r => r.json())
                .then(data => callback(data))
                .catch(e => callback({{error: e.toString()}}))
        """)
        print("Detail keys:", list(detail.keys()) if isinstance(detail, dict) else detail)
        detail_products = detail.get("data", {}).get("products", [])
        print("Detail products:", len(detail_products))
        if detail_products:
            opts = detail_products[0].get("options", [])
            print("Options sample:", opts[:3])

driver.quit()
