import re
import json
import time
import random
import requests
from urllib.parse import quote
from sqlalchemy.orm import Session
from app.models.mouse import Mouse
from app.models.keyboard import Keyboard
from app.models.monitor import Monitor
from app.models.headphones import Headphones
from app.models.microphone import Microphone
from app.models.mousepad import Mousepad

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "x-o3-app-name": "ozonweb",
    "x-o3-app-version": "5.0.0",
    "Accept": "application/json",
    "Accept-Language": "ru-RU,ru;q=0.9",
}

_BASE_URL = "https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2"

# ── Selenium session (lazy init, one driver per process) ──────────────────────

_driver = None


def _get_driver():
    global _driver
    if _driver is not None:
        try:
            _ = _driver.current_url
            return _driver
        except Exception:
            _driver = None

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
    stealth(driver, languages=["ru-RU", "ru"], vendor="Google Inc.",
            platform="Win32", webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine", fix_hairline=True)
    driver.set_script_timeout(30)
    driver.get("https://www.ozon.ru/")
    time.sleep(4)
    _driver = driver
    return _driver


def _browser_get(relative_url: str) -> dict | None:
    """Выполняет fetch() из контекста браузера и возвращает JSON или None."""
    driver = _get_driver()
    escaped = relative_url.replace("'", "\\'")
    result = driver.execute_async_script(f"""
        var callback = arguments[arguments.length - 1];
        fetch('{escaped}')
            .then(r => r.json())
            .then(data => callback(data))
            .catch(e => callback({{error: e.toString()}}))
    """)
    if isinstance(result, dict) and "error" not in result:
        return result
    return None

_MOUSE_KEYS = {
    "weight":           {"вес", "вес товара", "вес с упаковкой", "вес устройства", "масса"},
    "connection_types": {"тип соединения", "тип подключения", "интерфейс подключения"},
    "sensor":           {"тип датчика", "модель сенсора", "тип сенсора", "сенсор"},
    "switches":         {"тип переключателей", "переключатели", "микровыключатели"},
    "button_count":     {"количество кнопок"},
    "max_dpi":          {"макс. разрешение датчика, dpi", "максимальное разрешение", "разрешение датчика"},
    "color":            {"цвет"},
    "form_factor":      {"форма", "конструкция мыши"},
    "has_rgb":          {"подсветка", "rgb подсветка", "rgb-подсветка"},
}

_KEYBOARD_KEYS = {
    "switches":             {"тип переключателей", "переключатели", "тип свитчей"},
    "form_factor":          {"форм-фактор", "размер клавиатуры", "конструкция"},
    "board_material":       {"материал корпуса"},
    "keycap_material":      {"материал клавиш", "материал кейкапов"},
    "keycap_manufacturing": {"способ нанесения символов", "нанесение символов"},
    "connection_types":     {"тип подключения", "интерфейс"},
}

_MONITOR_KEYS = {
    "diagonal_inch":   {"диагональ экрана", "диагональ", "размер экрана"},
    "resolution":      {"разрешение экрана", "разрешение"},
    "refresh_rate_hz": {"частота обновления экрана", "частота обновления"},
    "matrix_type":     {"тип матрицы", "тип панели"},
}

_HEADPHONES_KEYS = {
    "construction_type":  {"конструкция", "тип конструкции"},
    "connection_types":   {"тип подключения", "интерфейс"},
    "has_microphone":     {"наличие микрофона", "микрофон"},
    "noise_cancellation": {"шумоподавление", "активное шумоподавление"},
}

_MICROPHONE_KEYS = {
    "mic_type":         {"тип микрофона", "тип капсюля"},
    "directionality":   {"направленность", "полярная диаграмма"},
    "connection_types": {"тип подключения", "интерфейс"},
    "frequency_range":  {"диапазон частот", "частотный диапазон"},
}

_MOUSEPAD_KEYS = {
    "size":             {"размер", "габариты"},
    "surface_material": {"материал поверхности", "материал"},
    "hardness":         {"жёсткость", "тип поверхности"},
    "has_rgb":          {"подсветка", "rgb-подсветка"},
}


def _parse_float(value: str) -> float | None:
    m = re.search(r"[\d]+[.,]?[\d]*", value)
    return float(m.group().replace(",", ".")) if m else None


def _parse_int(value: str) -> int | None:
    m = re.search(r"\d+", value)
    return int(m.group()) if m else None


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in ("да", "есть", "yes", "+", "true")


def _map_options(options: list[dict], keys_map: dict) -> dict:
    result: dict = {k: None for k in keys_map}
    for opt in options:
        name = opt.get("name", "").lower().strip()
        value = opt.get("value", "").strip()
        for field, key_set in keys_map.items():
            if name in key_set:
                result[field] = value
                break
    return result


def _map_mouse(options: list[dict]) -> dict:
    raw = _map_options(options, _MOUSE_KEYS)
    weight_str = raw.get("weight")
    weight_g = None
    if weight_str:
        val = _parse_float(weight_str)
        if val is not None:
            weight_g = round(val * 1000) if "кг" in weight_str.lower() else val
    button_str = raw.get("button_count")
    max_dpi_str = raw.get("max_dpi")
    has_rgb_str = raw.get("has_rgb")
    return {
        "weight_g":         weight_g,
        "connection_types": raw.get("connection_types"),
        "sensor":           raw.get("sensor"),
        "switches":         raw.get("switches"),
        "button_count":     _parse_int(button_str) if button_str else None,
        "max_dpi":          _parse_int(max_dpi_str) if max_dpi_str else None,
        "color":            raw.get("color"),
        "form_factor":      raw.get("form_factor"),
        "has_rgb":          _parse_bool(has_rgb_str) if has_rgb_str else False,
    }


def _map_keyboard(options: list[dict]) -> dict:
    return _map_options(options, _KEYBOARD_KEYS)


def _map_monitor(options: list[dict]) -> dict:
    raw = _map_options(options, _MONITOR_KEYS)
    return {
        "diagonal_inch":   _parse_float(raw["diagonal_inch"])   if raw["diagonal_inch"]   else None,
        "resolution":      raw["resolution"],
        "refresh_rate_hz": _parse_int(raw["refresh_rate_hz"])   if raw["refresh_rate_hz"] else None,
        "matrix_type":     raw["matrix_type"],
    }


def _map_headphones(options: list[dict]) -> dict:
    raw = _map_options(options, _HEADPHONES_KEYS)
    has_mic_str = raw.get("has_microphone")
    return {
        "construction_type":  raw.get("construction_type"),
        "connection_types":   raw.get("connection_types"),
        "has_microphone":     _parse_bool(has_mic_str) if has_mic_str else False,
        "noise_cancellation": raw.get("noise_cancellation"),
    }


def _map_microphone(options: list[dict]) -> dict:
    return _map_options(options, _MICROPHONE_KEYS)


def _map_mousepad(options: list[dict]) -> dict:
    raw = _map_options(options, _MOUSEPAD_KEYS)
    has_rgb_str = raw.get("has_rgb")
    return {
        "size":             raw.get("size"),
        "surface_material": raw.get("surface_material"),
        "hardness":         raw.get("hardness"),
        "has_rgb":          _parse_bool(has_rgb_str) if has_rgb_str else False,
    }


def _extract_products(widget_states: dict) -> list[dict]:
    for key, value in widget_states.items():
        if any(x in key for x in ("searchResultsV2", "tileGrid", "searchResults")):
            try:
                data = json.loads(value)
                items = data.get("items", [])
                if items:
                    return items
            except Exception:
                continue
    return []


def _parse_chars_from_widget_states(widget_states: dict) -> list[dict]:
    # Prefer the widget with the most characteristics (full list)
    best: list[dict] = []
    for key, value in widget_states.items():
        if "webCharacteristics" not in key and "webShortCharacteristics" not in key:
            continue
        try:
            data = json.loads(value) if isinstance(value, str) else value
            flat: list[dict] = []
            for group in data.get("characteristics", []):
                # features page: characteristics[0].short[] with {name, values[]}
                for item in group.get("short", []):
                    name = item.get("name", "")
                    vals = item.get("values", [])
                    text = "; ".join(v.get("text", "") for v in vals)
                    if name and text:
                        flat.append({"name": name, "value": text})
                # product page: characteristics[] with title.textRs + values[]
                title_rs = group.get("title", {}).get("textRs", [])
                name = title_rs[0].get("content", "") if title_rs else ""
                vals = group.get("values", [])
                text = "; ".join(v.get("text", "") for v in vals)
                if name and text:
                    flat.append({"name": name, "value": text})
            if len(flat) > len(best):
                best = flat
        except Exception:
            continue
    return best


def _search_ozon(query: str, limit: int = 50) -> list[dict]:
    all_products: list[dict] = []
    page = 1
    while len(all_products) < limit:
        api_url = (
            f"/api/entrypoint-api.bx/page/json/v2"
            f"?url=/search/?text={quote(query)}"
            f"&layout_container=categorySearchMegapagination&layout_page_index={page}"
        )
        try:
            data = _browser_get(api_url)
            if not data:
                break
            products = _extract_products(data.get("widgetStates", {}))
            if not products:
                break
            all_products.extend(products)
            page += 1
            time.sleep(random.uniform(0.5, 1.0))
        except Exception:
            break
    return all_products[:limit]


def _fetch_details(
    product_ids: list[int],
    url_map: dict[int, str],
) -> dict[int, list[dict]]:
    result: dict[int, list[dict]] = {}
    for pid in product_ids:
        product_url = url_map.get(pid)
        if not product_url:
            continue
        try:
            features_path = product_url.rstrip("/") + "/features/"
            api_url = f"/api/entrypoint-api.bx/page/json/v2?url={features_path}"
            data = _browser_get(api_url)
            if data:
                chars = _parse_chars_from_widget_states(data.get("widgetStates", {}))
                if chars:
                    result[pid] = chars
        except Exception:
            pass
        time.sleep(random.uniform(0.3, 0.7))
    return result


def _fetch_all(query: str, limit: int = 50) -> tuple[list[dict], dict[int, list[dict]]]:
    products = _search_ozon(query, limit)
    if not products:
        return [], {}

    url_map: dict = {}
    for p in products:
        pid = p.get("id")
        url = _get_url(p)
        if pid and url:
            url_map[str(pid)] = url

    details = _fetch_details(list(url_map.keys()), url_map)
    return products, details



def _get_name(product: dict) -> str:
    for state in product.get("mainState", []):
        if state.get("type") == "textAtom":
            atom = state.get("textAtom", {})
            test_id = atom.get("testInfo", {}).get("automatizationId", "")
            if "tile-name" in test_id or not test_id:
                text = atom.get("text", "")
                if text:
                    return text
    return ""


def _get_brand(product: dict) -> str:
    for state in product.get("mainState", []):
        if state.get("type") == "labelListV2":
            items = state.get("labelListV2", {}).get("items", [])
            for item in items:
                if item.get("type") == "text":
                    text = item.get("text", {}).get("text", "")
                    if text:
                        return text
    return ""


def _get_price(product: dict) -> float:
    for state in product.get("mainState", []):
        if state.get("type") == "priceV2":
            price_list = state.get("priceV2", {}).get("price", [])
            for p in price_list:
                if p.get("textStyle") == "PRICE":
                    raw = re.sub(r"[^\d]", "", p.get("text", ""))
                    if raw:
                        try:
                            return float(raw)
                        except ValueError:
                            pass
    return 0.0


def _get_image(product: dict) -> str | None:
    tile = product.get("tileImage", {})
    items = tile.get("items", []) if isinstance(tile, dict) else []
    for item in items:
        if item.get("type") == "image":
            link = item.get("image", {}).get("link", "")
            if link:
                return link
    return None


def _get_url(product: dict) -> str:
    link = product.get("action", {}).get("link", "")
    return link.split("?")[0]


def _run_parse(db: Session, query: str, model_class, char_mapper, limit: int = 8) -> dict:
    added = updated = failed = 0
    try:
        products, details = _fetch_all(query, limit)
    except Exception as e:
        return {"added": 0, "updated": 0, "failed": 0, "error": str(e)}

    if not products:
        return {"added": 0, "updated": 0, "failed": 0}

    for product in products:
        try:
            pid = product.get("id")
            if not pid:
                continue
            ozon_sku = str(pid)
            name = _get_name(product)
            brand = _get_brand(product)
            price = _get_price(product)
            image_url = _get_image(product)
            product_url = _get_url(product)
            ozon_url = f"https://www.ozon.ru{product_url}" if product_url.startswith("/") else product_url

            chars = char_mapper(details.get(str(pid), []))

            existing = db.query(model_class).filter(model_class.ozon_sku == ozon_sku).first()
            if existing:
                existing.price = price
                if image_url:
                    existing.image_url = image_url
                for field, value in chars.items():
                    if value is not None:
                        setattr(existing, field, value)
                db.commit()
                updated += 1
            else:
                db.add(model_class(
                    name=name,
                    brand=brand,
                    price=price,
                    ozon_sku=ozon_sku,
                    ozon_url=ozon_url,
                    image_url=image_url,
                    **chars,
                ))
                db.commit()
                added += 1
        except Exception:
            failed += 1
            db.rollback()

    return {"added": added, "updated": updated, "failed": failed}


def _backfill(db: Session, model_class, char_mapper, null_field: str) -> dict:
    rows = db.query(model_class).filter(
        getattr(model_class, null_field) == None,
        model_class.ozon_sku != None,
    ).all()

    url_map: dict[int, str] = {}
    for row in rows:
        if row.ozon_sku and row.ozon_sku.isdigit() and row.ozon_url:
            pid = int(row.ozon_sku)
            path = row.ozon_url.replace("https://www.ozon.ru", "")
            url_map[pid] = path

    details = _fetch_details(list(url_map.keys()), url_map)
    updated = failed = skipped = 0

    for row in rows:
        if not row.ozon_sku or not row.ozon_sku.isdigit():
            skipped += 1
            continue
        pid = int(row.ozon_sku)
        opts = details.get(pid)
        if not opts:
            skipped += 1
            continue
        try:
            chars = char_mapper(opts)
            for field, value in chars.items():
                if value is not None:
                    setattr(row, field, value)
            db.commit()
            updated += 1
        except Exception:
            failed += 1
            db.rollback()

    return {"updated": updated, "failed": failed, "skipped": skipped}


def parse_mice(db: Session) -> dict:
    queries = [
        "игровая мышь проводная",
        "игровая мышь беспроводная",
        "мышь logitech игровая",
        "мышь razer игровая",
        "мышь steelseries",
        "мышь gaming rgb",
        "мышь офисная беспроводная",
    ]
    total = {"added": 0, "updated": 0, "failed": 0}
    for q in queries:
        r = _run_parse(db, q, Mouse, _map_mouse, limit=8)
        if "error" in r:
            continue
        total["added"] += r.get("added", 0)
        total["updated"] += r.get("updated", 0)
        total["failed"] += r.get("failed", 0)
        import time as _t; _t.sleep(1)
    return total

def parse_keyboards(db: Session) -> dict:
    return _run_parse(db, "механическая клавиатура игровая", Keyboard, _map_keyboard)

def parse_monitors(db: Session) -> dict:
    return _run_parse(db, "игровой монитор", Monitor, _map_monitor)

def parse_headphones(db: Session) -> dict:
    return _run_parse(db, "игровые наушники гарнитура", Headphones, _map_headphones)

def parse_microphones(db: Session) -> dict:
    return _run_parse(db, "usb микрофон компьютер", Microphone, _map_microphone)

def parse_mousepads(db: Session) -> dict:
    return _run_parse(db, "игровой коврик для мыши", Mousepad, _map_mousepad)


def backfill_mice(db: Session) -> dict:
    return _backfill(db, Mouse, _map_mouse, "sensor")

def backfill_keyboards(db: Session) -> dict:
    return _backfill(db, Keyboard, _map_keyboard, "switches")

def backfill_monitors(db: Session) -> dict:
    return _backfill(db, Monitor, _map_monitor, "matrix_type")

def backfill_headphones(db: Session) -> dict:
    return _backfill(db, Headphones, _map_headphones, "connection_types")

def backfill_microphones(db: Session) -> dict:
    return _backfill(db, Microphone, _map_microphone, "mic_type")

def backfill_mousepads(db: Session) -> dict:
    return _backfill(db, Mousepad, _map_mousepad, "hardness")
