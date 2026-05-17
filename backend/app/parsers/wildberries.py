import re
import time
import json
import random
import concurrent.futures
import requests
from urllib.parse import quote
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager
from sqlalchemy.orm import Session
from app.models.mouse import Mouse
from app.models.keyboard import Keyboard
from app.models.monitor import Monitor
from app.models.headphones import Headphones
from app.models.microphone import Microphone
from app.models.mousepad import Mousepad

# ── Ключи характеристик WB (русские названия полей из options) ─────────────────

_MOUSE_KEYS = {
    "weight":           {"вес с упаковкой (кг)", "вес мыши", "вес", "масса"},
    "connection_types": {"тип подключения мыши", "тип подключения", "интерфейс"},
    "sensor":           {"тип датчика мыши", "сенсор", "тип сенсора"},
    "switches":         {"переключатели кнопок мыши", "переключатели", "микровыключатели"},
}

_KEYBOARD_KEYS = {
    "switches":             {"тип переключателей клавиатуры", "переключатели", "тип переключателей"},
    "form_factor":          {"форм-фактор клавиатуры", "форм-фактор", "конструкция"},
    "board_material":       {"материал корпуса клавиатуры", "материал корпуса"},
    "keycap_material":      {"материал клавиш", "материал кейкапов", "материал колпачков"},
    "keycap_manufacturing": {"способ нанесения символов клавиатуры", "способ нанесения символов", "нанесение символов"},
    "connection_types":     {"тип подключения клавиатуры", "тип подключения", "интерфейс"},
}

_MONITOR_KEYS = {
    "diagonal_inch":   {"диагональ монитора", "диагональ", "размер экрана"},
    "resolution":      {"разрешение экрана", "разрешение"},
    "refresh_rate_hz": {"частота обновления экрана", "частота обновления", "максимальная частота обновления"},
    "matrix_type":     {"тип матрицы", "тип панели"},
}

_HEADPHONES_KEYS = {
    "construction_type":  {"конструкция наушников", "конструкция", "тип конструкции"},
    "connection_types":   {"тип подключения наушников", "тип подключения", "интерфейс"},
    "has_microphone":     {"микрофон", "встроенный микрофон"},
    "noise_cancellation": {"шумоподавление", "активное шумоподавление"},
}

_MICROPHONE_KEYS = {
    "mic_type":         {"тип микрофона", "тип капсюля"},
    "directionality":   {"направленность микрофона", "направленность", "полярная диаграмма"},
    "connection_types": {"тип подключения микрофона", "тип подключения", "интерфейс"},
    "frequency_range":  {"диапазон частот", "частотный диапазон"},
}

_MOUSEPAD_KEYS = {
    "size":             {"размер коврика", "размер", "габариты"},
    "surface_material": {"материал поверхности коврика", "материал поверхности", "материал"},
    "hardness":         {"жёсткость коврика", "жёсткость", "тип поверхности"},
    "has_rgb":          {"подсветка коврика", "подсветка", "rgb-подсветка"},
}

# ── Вспомогательные парсеры значений ──────────────────────────────────────────

def _parse_float(value: str) -> float | None:
    m = re.search(r"[\d]+[.,]?[\d]*", value)
    return float(m.group().replace(",", ".")) if m else None


def _parse_int(value: str) -> int | None:
    m = re.search(r"\d+", value)
    return int(m.group()) if m else None


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in ("да", "есть", "yes", "+", "true")


# ── Общий маппер: options → dict ──────────────────────────────────────────────

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


# ── Маппер характеристик для каждой категории ─────────────────────────────────

def _map_mouse(options: list[dict]) -> dict:
    raw = _map_options(options, _MOUSE_KEYS)
    weight_str = raw.get("weight")
    weight_g = None
    if weight_str:
        val = _parse_float(weight_str)
        if val is not None:
            # WB отдаёт вес в кг (напр. "0.25 кг") — конвертируем в граммы
            weight_g = round(val * 1000) if "кг" in weight_str.lower() else val
    return {
        "weight_g":         weight_g,
        "connection_types": raw.get("connection_types"),
        "sensor":           raw.get("sensor"),
        "switches":         raw.get("switches"),
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


# ── URL-строители ──────────────────────────────────────────────────────────────

def _build_search_url(query: str) -> str:
    return (
        "https://www.wildberries.ru/__internal/u-search/exactmatch/ru/common/v18/search"
        f"?ab_testing=false&appType=1&curr=rub&dest=-1257786"
        f"&query={quote(query)}&resultset=catalog&sort=popular&spp=30&suppressSpellcheck=false"
    )


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


# ── Selenium: список товаров из поиска WB ─────────────────────────────────────

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


def _fetch_wb_products(query: str, limit: int = 100) -> list[dict]:
    driver = _make_driver()
    search_url = _build_search_url(query)
    try:
        driver.get("https://www.wildberries.ru/")
        time.sleep(5)
        result = driver.execute_async_script(f"""
            var callback = arguments[arguments.length - 1];
            fetch('{search_url}')
                .then(r => r.json())
                .then(data => callback(data))
                .catch(e => callback({{error: e.toString()}}))
        """)
        if not isinstance(result, dict) or "error" in result:
            return []
        return result.get("products", [])[:limit]
    finally:
        driver.quit()


# ── Requests: характеристики из detail API (минует CORS) ──────────────────────

_DETAIL_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://www.wildberries.ru/",
}


def _fetch_details(product_ids: list[int]) -> dict[int, list[dict]]:
    result: dict[int, list[dict]] = {}
    for i in range(0, len(product_ids), 20):
        batch = product_ids[i:i + 20]
        nm = ";".join(str(pid) for pid in batch)
        url = f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&nm={nm}"
        try:
            resp = requests.get(url, headers=_DETAIL_HEADERS, timeout=15)
            if resp.status_code == 200:
                for p in resp.json().get("data", {}).get("products", []):
                    result[p["id"]] = p.get("options", [])
        except Exception:
            pass
        time.sleep(0.3)
    return result


# ── Совместимость с тестами (старый интерфейс) ────────────────────────────────

def _search_wb(query: str, limit: int = 100) -> list[dict]:
    return _fetch_wb_products(query, limit)


# ── Характеристики через CDN WB (basket-XX.wbbasket.ru/…/card.json) ──────────

def _build_card_json_url(product_id: int) -> str:
    vol = product_id // 100000
    part = product_id // 1000
    basket = _get_basket(vol)
    return f"https://basket-{basket}.wbbasket.ru/vol{vol}/part{part}/{product_id}/info/ru/card.json"


def _fetch_details(product_ids: list[int]) -> dict[int, list[dict]]:
    """
    Получает характеристики товаров напрямую с CDN WB (card.json).
    Не требует авторизации и обходит блокировки card.wb.ru.
    """
    result: dict[int, list[dict]] = {}
    for pid in product_ids:
        url = _build_card_json_url(pid)
        try:
            resp = requests.get(url, headers=_DETAIL_HEADERS, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                options = data.get("options", data.get("grouped_params", []))
                result[pid] = options
        except Exception:
            pass
        time.sleep(random.uniform(0.3, 0.8))
    return result


# ── Единая функция: продукты + характеристики ─────────────────────────────────

def _fetch_all(query: str, limit: int = 50) -> tuple[list[dict], dict[int, list[dict]]]:
    """
    Список товаров — через поисковый API WB (Selenium, один запуск).
    Характеристики — напрямую с CDN basket-XX.wbbasket.ru через requests.
    """
    driver = _make_driver()
    driver.set_script_timeout(30)
    try:
        driver.get("https://www.wildberries.ru/")
        time.sleep(5)

        search_url = _build_search_url(query)
        result = driver.execute_async_script(f"""
            var callback = arguments[arguments.length - 1];
            fetch('{search_url}')
                .then(r => r.json())
                .then(data => callback(data))
                .catch(e => callback({{error: e.toString()}}))
        """)
        if not isinstance(result, dict) or "error" in result:
            return [], {}
        products = result.get("products", [])[:limit]
    finally:
        driver.quit()

    if not products:
        return [], {}

    details = _fetch_details([p["id"] for p in products])
    if products:
        pid0 = products[0]["id"]
        all_opts = details.get(pid0, [])
        print(f"[WB-DEBUG] pid={pid0} opts={len(all_opts)}", flush=True)
        for o in all_opts:
            print(f"[WB-OPT] {o.get('name')!r:40s} -> {o.get('value')!r}", flush=True)

    return products, details


def _fetch_details_with_cookies(
    product_ids: list[int], cookies: dict
) -> dict[int, list[dict]]:
    """Оставлен для обратной совместимости с тестами."""
    return {}


# ── Общая функция парсинга категории ──────────────────────────────────────────

def _run_parse(db: Session, query: str, model_class, char_mapper) -> dict:
    added = updated = failed = 0

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            products, wb_cookies = executor.submit(_fetch_all, query).result(timeout=360)
    except Exception as e:
        return {"added": 0, "updated": 0, "failed": 0, "error": str(e)}

    details = _fetch_details_with_cookies([p["id"] for p in products], wb_cookies) if products else {}

    if not products:
        return {"added": 0, "updated": 0, "failed": 0}

    for product in products:
        try:
            pid = product["id"]
            wb_sku = str(pid)
            name = product.get("name", "")
            brand = product.get("brand", "")
            sizes = product.get("sizes", [])
            price_raw = sizes[0].get("price", {}).get("product", 0) if sizes else 0
            price = price_raw / 100

            chars = char_mapper(details.get(pid, []))

            existing = db.query(model_class).filter(model_class.wb_sku == wb_sku).first()
            if existing:
                existing.price = price
                existing.image_url = _build_image_url(pid)
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
                    wb_sku=wb_sku,
                    wb_url=f"https://www.wildberries.ru/catalog/{pid}/detail.aspx",
                    image_url=_build_image_url(pid),
                    **chars,
                ))
                db.commit()
                added += 1
        except Exception:
            failed += 1
            db.rollback()

    return {"added": added, "updated": updated, "failed": failed}


# ── Публичные функции парсинга ─────────────────────────────────────────────────

def parse_mice(db: Session) -> dict:
    return _run_parse(db, "игровая мышь", Mouse, _map_mouse)


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
