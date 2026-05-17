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

_MOUSE_KEYS = {
    "weight":           {"вес", "вес товара", "вес с упаковкой", "вес устройства"},
    "connection_types": {"тип подключения", "интерфейс подключения", "интерфейс"},
    "sensor":           {"тип сенсора", "сенсор", "тип датчика"},
    "switches":         {"тип переключателей", "переключатели", "микровыключатели"},
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
    for key, value in widget_states.items():
        if any(x in key for x in ("webCharacteristics", "webDetailSKU", "characteristics")):
            try:
                data = json.loads(value)
                flat: list[dict] = []
                for group in data.get("characteristics", []):
                    for char in group.get("short_characteristics", []):
                        name = char.get("name", "")
                        vals = char.get("values", [])
                        text = "; ".join(v.get("text", "") for v in vals)
                        flat.append({"name": name, "value": text})
                if flat:
                    return flat
            except Exception:
                continue
    return []


def _search_ozon(query: str, limit: int = 50) -> list[dict]:
    url = f"/search/?text={quote(query)}&layout_container=categorySearchMegapagination&layout_page_index=1"
    try:
        resp = requests.get(_BASE_URL, params={"url": url}, headers=_HEADERS, timeout=30)
        if resp.status_code != 200:
            return []
        data = resp.json()
        products = _extract_products(data.get("widgetStates", {}))
        return products[:limit]
    except Exception:
        return []


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
            resp = requests.get(
                _BASE_URL,
                params={"url": product_url},
                headers=_HEADERS,
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                chars = _parse_chars_from_widget_states(data.get("widgetStates", {}))
                if chars:
                    result[pid] = chars
        except Exception:
            pass
        time.sleep(random.uniform(0.5, 1.0))
    return result


def _fetch_all(query: str, limit: int = 50) -> tuple[list[dict], dict[int, list[dict]]]:
    products = _search_ozon(query, limit)
    if not products:
        return [], {}

    url_map: dict[int, str] = {}
    for p in products:
        pid = p.get("id")
        url = p.get("urlForProduct") or p.get("action", {}).get("link", "")
        if pid and url:
            url_map[pid] = url

    details = _fetch_details(list(url_map.keys()), url_map)
    return products, details


def _get_price(product: dict) -> float:
    for key in ("finalPrice", "price", "cardPrice"):
        val = product.get(key)
        if val is not None:
            try:
                return float(str(val).replace(" ", "").replace(" ", "").replace(",", "."))
            except ValueError:
                continue
    for state in product.get("mainState", []):
        atom = state.get("atom", {})
        price_info = atom.get("price", {})
        if price_info:
            raw = price_info.get("price", "") or price_info.get("originalPrice", "")
            m = re.search(r"[\d]+[.,]?[\d]*", str(raw).replace(" ", ""))
            if m:
                return float(m.group().replace(",", "."))
    return 0.0


def _get_image(product: dict) -> str | None:
    images = product.get("images", [])
    if images:
        return images[0] if isinstance(images[0], str) else images[0].get("url")
    cover = product.get("coverImage")
    return cover if isinstance(cover, str) else None


def _run_parse(db: Session, query: str, model_class, char_mapper) -> dict:
    added = updated = failed = 0
    try:
        products, details = _fetch_all(query)
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
            name = product.get("name", "")
            brand = product.get("brand", "")
            price = _get_price(product)
            image_url = _get_image(product)
            product_url = product.get("urlForProduct") or product.get("action", {}).get("link", "")
            ozon_url = f"https://www.ozon.ru{product_url}" if product_url.startswith("/") else product_url

            chars = char_mapper(details.get(pid, []))

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
