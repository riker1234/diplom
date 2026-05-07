import re
import time
import concurrent.futures
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager
from sqlalchemy.orm import Session
from app.models.mouse import Mouse

_WEIGHT_KEYS = {"вес", "масса"}
_CONNECTION_KEYS = {"тип подключения", "интерфейс"}
_SENSOR_KEYS = {"сенсор", "тип сенсора"}
_SWITCH_KEYS = {"переключатели", "микровыключатели"}

_SEARCH_URL = (
    "https://www.wildberries.ru/__internal/u-search/exactmatch/ru/common/v18/search"
    "?ab_testing=false&appType=1&curr=rub&dest=-1257786"
    "&query=%D0%B8%D0%B3%D1%80%D0%BE%D0%B2%D0%B0%D1%8F+%D0%BC%D1%8B%D1%88%D1%8C"
    "&resultset=catalog&sort=popular&spp=30&suppressSpellcheck=false"
)


def _parse_weight(value: str) -> float | None:
    match = re.search(r"[\d]+[.,]?[\d]*", value)
    if match:
        return float(match.group().replace(",", "."))
    return None


def _map_mouse_characteristics(options: list[dict]) -> dict:
    result = {"weight_g": None, "connection_types": None, "sensor": None, "switches": None}
    for opt in options:
        name = opt.get("name", "").lower().strip()
        value = opt.get("value", "").strip()
        if name in _WEIGHT_KEYS:
            result["weight_g"] = _parse_weight(value)
        elif name in _CONNECTION_KEYS:
            result["connection_types"] = value
        elif name in _SENSOR_KEYS:
            result["sensor"] = value
        elif name in _SWITCH_KEYS:
            result["switches"] = value
    return result


def _get_basket(vol: int) -> str:
    thresholds = [
        143, 287, 431, 719, 1007, 1061, 1115, 1169, 1313, 1601,
        1655, 1919, 2045, 2189, 2405, 2621, 2837, 3053, 3269, 3485,
        3701, 3917, 4133, 4349,
    ]
    for i, t in enumerate(thresholds):
        if vol <= t:
            return str(i + 1).zfill(2)
    return "25"


def _build_image_url(product_id: int) -> str:
    vol = product_id // 100000
    part = product_id // 1000
    basket = _get_basket(vol)
    return f"https://basket-{basket}.wbbasket.ru/vol{vol}/part{part}/{product_id}/images/big/1.webp"


def _make_driver() -> webdriver.Chrome:
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
    return driver


def _fetch_wb_products(limit: int = 100) -> list[dict]:
    driver = _make_driver()
    try:
        driver.get("https://www.wildberries.ru/")
        time.sleep(5)
        result = driver.execute_async_script(f"""
            var callback = arguments[arguments.length - 1];
            fetch('{_SEARCH_URL}')
                .then(r => r.json())
                .then(data => callback(data))
                .catch(e => callback({{error: e.toString()}}))
        """)
        if "error" in result:
            return []
        return result.get("products", [])[:limit]
    finally:
        driver.quit()


# Оставляем для совместимости с тестами
def _search_wb(query: str, limit: int = 100) -> list[dict]:
    return _fetch_wb_products(limit)


def _fetch_details(product_ids: list[int]) -> list[dict]:
    return []


def parse_mice(db: Session) -> dict:
    added = updated = failed = 0

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_fetch_wb_products)
            products = future.result(timeout=90)
    except Exception as e:
        return {"added": 0, "updated": 0, "failed": 0, "error": str(e)}

    if not products:
        return {"added": 0, "updated": 0, "failed": 0}

    for product in products:
        try:
            pid = product["id"]
            wb_sku = str(pid)
            name = product.get("name", "")
            brand = product.get("brand", "")
            weight_kg = product.get("weight")
            weight_g = round(weight_kg * 1000, 1) if weight_kg else None
            sizes = product.get("sizes", [])
            price_raw = sizes[0].get("price", {}).get("product", 0) if sizes else 0
            price = price_raw / 100

            existing = db.query(Mouse).filter(Mouse.wb_sku == wb_sku).first()
            if existing:
                existing.price = price
                existing.image_url = _build_image_url(pid)
                db.commit()
                updated += 1
            else:
                db.add(Mouse(
                    name=name,
                    brand=brand,
                    price=price,
                    wb_sku=wb_sku,
                    wb_url=f"https://www.wildberries.ru/catalog/{pid}/detail.aspx",
                    image_url=_build_image_url(pid),
                    weight_g=weight_g,
                    connection_types=None,
                    sensor=None,
                    switches=None,
                ))
                db.commit()
                added += 1
        except Exception:
            failed += 1
            db.rollback()

    return {"added": added, "updated": updated, "failed": failed}
