import re
import time
import random
import threading
from urllib.parse import quote
from difflib import SequenceMatcher
from sqlalchemy.orm import Session
from app.models.mouse import Mouse
from app.models.keyboard import Keyboard
from app.models.monitor import Monitor
from app.models.headphones import Headphones
from app.models.microphone import Microphone
from app.models.mousepad import Mousepad
from app.parsers.browser import new_context

_BASE = "https://www.dns-shop.ru"

_page_lock = threading.Lock()
_dns_ctx = None
_dns_page = None


def _get_dns_page():
    global _dns_ctx, _dns_page
    with _page_lock:
        if _dns_page is not None:
            try:
                _ = _dns_page.url
                return _dns_page
            except Exception:
                pass
        _dns_ctx = new_context()
        _dns_page = _dns_ctx.new_page()
        try:
            _dns_page.goto(_BASE, wait_until="domcontentloaded", timeout=30000)
        except Exception:
            pass
    return _dns_page


# ── Helpers ────────────────────────────────────────────────────────────────────

def _parse_float(value: str) -> float | None:
    m = re.search(r"[\d]+[.,]?[\d]*", value)
    return float(m.group().replace(",", ".")) if m else None


def _parse_int(value: str) -> int | None:
    m = re.search(r"\d+", value)
    return int(m.group()) if m else None


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in ("да", "есть", "yes", "+", "true")


def _name_similarity(a: str, b: str) -> float:
    a = re.sub(r"\s+", " ", a.lower().strip())
    b = re.sub(r"\s+", " ", b.lower().strip())
    return SequenceMatcher(None, a, b).ratio()


# ── DNS search via Playwright ──────────────────────────────────────────────────

def _search_dns(query: str, limit: int = 8) -> list[dict]:
    results = []
    page_num = 1
    page = _get_dns_page()
    while len(results) < limit:
        try:
            url = f"{_BASE}/search/?q={quote(query)}&p={page_num}"
            page.goto(url, wait_until="networkidle", timeout=30000)
            data = page.evaluate("() => window.__NEXT_DATA__ || null")
            if not data:
                break
            products = _extract_dns_products(data)
            if not products:
                break
            results.extend(products)
            page_num += 1
            time.sleep(random.uniform(0.5, 1.0))
        except Exception:
            break
    return results[:limit]


def _extract_dns_products(data: dict) -> list[dict]:
    try:
        props = data.get("props", {}).get("initialState", {})
        for path in [["search", "products"], ["catalog", "products"], ["products"]]:
            node = props
            for key in path:
                node = node.get(key, {}) if isinstance(node, dict) else {}
            if isinstance(node, list) and node:
                return node
    except Exception:
        pass
    return []


def _get_dns_characteristics(product_url: str) -> list[dict]:
    page = _get_dns_page()
    try:
        url = product_url.rstrip("/") + "/characteristics/"
        page.goto(url, wait_until="networkidle", timeout=30000)
        data = page.evaluate("() => window.__NEXT_DATA__ || null")
        if not data:
            return []
        return _extract_dns_chars(data)
    except Exception:
        return []


def _extract_dns_chars(data: dict) -> list[dict]:
    flat = []
    try:
        props = data.get("props", {}).get("initialState", {})
        product = (
            props.get("product", {})
            or props.get("productCard", {}).get("product", {})
        )
        chars = product.get("characteristics") or product.get("properties") or []
        for group in chars:
            if isinstance(group, dict):
                items = group.get("items") or group.get("properties") or []
                for item in items:
                    name = item.get("name") or item.get("title") or ""
                    value = item.get("value") or ""
                    if isinstance(value, list):
                        value = "; ".join(str(v) for v in value)
                    if name and value:
                        flat.append({"name": str(name), "value": str(value)})
    except Exception:
        pass
    return flat


# ── Key maps (DNS field names) ─────────────────────────────────────────────────

_DNS_MOUSE_KEYS = {
    "weight":           {"вес", "вес устройства"},
    "connection_types": {"тип подключения"},
    "interface":        {"интерфейс"},
    "sensor":           {"тип сенсора", "сенсор", "оптический сенсор"},
    "switches":         {"тип переключателей", "переключатели"},
    "button_count":     {"количество кнопок"},
    "max_dpi":          {"максимальное разрешение", "разрешение сенсора"},
    "color":            {"цвет"},
    "form_factor":      {"для кого", "форм-фактор"},
    "has_rgb":          {"подсветка"},
}

_DNS_KEYBOARD_KEYS = {
    "switches":             {"тип переключателей", "переключатели"},
    "form_factor":          {"форм-фактор", "тип"},
    "board_material":       {"материал корпуса"},
    "keycap_material":      {"материал клавиш"},
    "keycap_manufacturing": {"нанесение символов"},
    "connection_types":     {"тип подключения"},
    "interface":            {"интерфейс"},
    "has_rgb":              {"подсветка"},
    "layout":               {"раскладка"},
    "key_count":            {"количество клавиш"},
    "color":                {"цвет"},
}

_DNS_MONITOR_KEYS = {
    "diagonal_inch":    {"диагональ экрана", "диагональ"},
    "resolution":       {"разрешение"},
    "refresh_rate_hz":  {"частота обновления", "максимальная частота"},
    "matrix_type":      {"тип матрицы", "технология матрицы"},
    "response_time_ms": {"время отклика"},
    "brightness_nits":  {"яркость"},
    "hdr":              {"поддержка hdr", "hdr"},
    "color":            {"цвет"},
}

_DNS_HEADPHONES_KEYS = {
    "construction_type":  {"конструкция", "тип"},
    "connection_types":   {"тип подключения"},
    "interface":          {"интерфейс"},
    "has_microphone":     {"микрофон", "наличие микрофона"},
    "noise_cancellation": {"шумоподавление"},
    "freq_min":           {"минимальная частота"},
    "freq_max":           {"максимальная частота"},
    "impedance_ohm":      {"импеданс", "сопротивление"},
    "color":              {"цвет"},
    "has_rgb":            {"подсветка"},
}

_DNS_MICROPHONE_KEYS = {
    "mic_type":         {"тип микрофона", "тип капсюля"},
    "directionality":   {"направленность", "диаграмма направленности"},
    "connection_types": {"тип подключения"},
    "interface":        {"интерфейс"},
    "frequency_range":  {"диапазон частот"},
    "sample_rate":      {"частота дискретизации"},
    "bit_depth":        {"разрядность"},
    "color":            {"цвет"},
}

_DNS_MOUSEPAD_KEYS = {
    "size":             {"размер"},
    "surface_material": {"материал поверхности", "материал"},
    "hardness":         {"жёсткость"},
    "has_rgb":          {"подсветка"},
    "color":            {"цвет"},
    "thickness_mm":     {"толщина"},
}


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


def _map_mouse_dns(options: list[dict]) -> dict:
    raw = _map_options(options, _DNS_MOUSE_KEYS)
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
        "interface":        raw.get("interface"),
        "sensor":           raw.get("sensor"),
        "switches":         raw.get("switches"),
        "button_count":     _parse_int(button_str) if button_str else None,
        "max_dpi":          _parse_int(max_dpi_str) if max_dpi_str else None,
        "color":            raw.get("color"),
        "form_factor":      raw.get("form_factor"),
        "has_rgb":          _parse_bool(has_rgb_str) if has_rgb_str else False,
    }


def _map_keyboard_dns(options: list[dict]) -> dict:
    raw = _map_options(options, _DNS_KEYBOARD_KEYS)
    has_rgb_str = raw.get("has_rgb")
    key_count_str = raw.get("key_count")
    return {
        "switches":             raw.get("switches"),
        "form_factor":          raw.get("form_factor"),
        "board_material":       raw.get("board_material"),
        "keycap_material":      raw.get("keycap_material"),
        "keycap_manufacturing": raw.get("keycap_manufacturing"),
        "connection_types":     raw.get("connection_types"),
        "interface":            raw.get("interface"),
        "has_rgb":              _parse_bool(has_rgb_str) if has_rgb_str else False,
        "layout":               raw.get("layout"),
        "key_count":            _parse_int(key_count_str) if key_count_str else None,
        "color":                raw.get("color"),
    }


def _map_monitor_dns(options: list[dict]) -> dict:
    raw = _map_options(options, _DNS_MONITOR_KEYS)
    hdr_str = raw.get("hdr")
    brightness_str = raw.get("brightness_nits")
    response_str = raw.get("response_time_ms")
    return {
        "diagonal_inch":    _parse_float(raw["diagonal_inch"])  if raw["diagonal_inch"]  else None,
        "resolution":       raw["resolution"],
        "refresh_rate_hz":  _parse_int(raw["refresh_rate_hz"])  if raw["refresh_rate_hz"] else None,
        "matrix_type":      raw["matrix_type"],
        "response_time_ms": _parse_float(response_str) if response_str else None,
        "brightness_nits":  _parse_int(brightness_str) if brightness_str else None,
        "hdr":              _parse_bool(hdr_str) if hdr_str else False,
        "color":            raw.get("color"),
    }


def _map_headphones_dns(options: list[dict]) -> dict:
    raw = _map_options(options, _DNS_HEADPHONES_KEYS)
    has_mic_str = raw.get("has_microphone")
    has_rgb_str = raw.get("has_rgb")
    freq_min = raw.get("freq_min")
    freq_max = raw.get("freq_max")
    if freq_min and freq_max:
        freq_min_val = _parse_int(freq_min)
        freq_max_val = _parse_int(freq_max)
        frequency_response = f"{freq_min_val}-{freq_max_val}" if freq_min_val and freq_max_val else None
    else:
        frequency_response = freq_min or freq_max
    imp_str = raw.get("impedance_ohm")
    return {
        "construction_type":  raw.get("construction_type"),
        "connection_types":   raw.get("connection_types"),
        "interface":          raw.get("interface"),
        "has_microphone":     _parse_bool(has_mic_str) if has_mic_str else False,
        "noise_cancellation": raw.get("noise_cancellation"),
        "frequency_response": frequency_response,
        "impedance_ohm":      _parse_int(imp_str) if imp_str else None,
        "color":              raw.get("color"),
        "has_rgb":            _parse_bool(has_rgb_str) if has_rgb_str else False,
    }


def _map_microphone_dns(options: list[dict]) -> dict:
    raw = _map_options(options, _DNS_MICROPHONE_KEYS)
    return {
        "mic_type":         raw.get("mic_type"),
        "directionality":   raw.get("directionality"),
        "connection_types": raw.get("connection_types"),
        "interface":        raw.get("interface"),
        "frequency_range":  raw.get("frequency_range"),
        "sample_rate":      raw.get("sample_rate"),
        "bit_depth":        raw.get("bit_depth"),
        "color":            raw.get("color"),
    }


def _map_mousepad_dns(options: list[dict]) -> dict:
    raw = _map_options(options, _DNS_MOUSEPAD_KEYS)
    has_rgb_str = raw.get("has_rgb")
    thickness_str = raw.get("thickness_mm")
    return {
        "size":             raw.get("size"),
        "surface_material": raw.get("surface_material"),
        "hardness":         raw.get("hardness"),
        "has_rgb":          _parse_bool(has_rgb_str) if has_rgb_str else False,
        "color":            raw.get("color"),
        "thickness_mm":     _parse_float(thickness_str) if thickness_str else None,
    }


# ── Core parse logic ───────────────────────────────────────────────────────────

def _run_dns_parse(
    db: Session,
    query: str,
    model_class,
    char_mapper,
    dns_product_to_dict=None,
    required_fields: list[str] | None = None,
    limit: int = 8,
) -> dict:
    added = updated = failed = skipped = 0

    try:
        products = _search_dns(query, limit)
    except Exception as e:
        return {"added": 0, "updated": 0, "failed": 0, "skipped": 0, "error": str(e)}

    for raw_product in products:
        try:
            dns_sku = str(raw_product.get("id") or raw_product.get("code") or "")
            name = raw_product.get("name") or raw_product.get("title") or ""
            brand = raw_product.get("brand") or ""
            dns_price = float(raw_product.get("price") or raw_product.get("minPrice") or 0) or None
            product_url = raw_product.get("url") or raw_product.get("link") or ""
            if product_url and not product_url.startswith("http"):
                product_url = _BASE + product_url
            dns_url = product_url

            if not dns_sku or not name:
                skipped += 1
                continue

            chars = char_mapper(_get_dns_characteristics(product_url))

            existing = db.query(model_class).filter(model_class.dns_sku == dns_sku).first()
            if existing:
                existing.dns_price = dns_price
                for field, value in chars.items():
                    if value is not None:
                        setattr(existing, field, value)
                db.commit()
                updated += 1
                continue

            matched = _find_by_name(db, model_class, name, brand)
            if matched:
                matched.dns_sku = dns_sku
                matched.dns_url = dns_url
                matched.dns_price = dns_price
                for field, value in chars.items():
                    if value is not None:
                        setattr(matched, field, value)
                db.commit()
                updated += 1
            else:
                if required_fields and all(chars.get(f) is None for f in required_fields):
                    skipped += 1
                    continue
                db.add(model_class(
                    name=name,
                    brand=brand or None,
                    dns_sku=dns_sku,
                    dns_url=dns_url,
                    dns_price=dns_price,
                    **chars,
                ))
                db.commit()
                added += 1
        except Exception:
            failed += 1
            db.rollback()
        time.sleep(random.uniform(0.3, 0.7))

    return {"added": added, "updated": updated, "failed": failed, "skipped": skipped}


def _find_by_name(db, model_class, name: str, brand: str, threshold: float = 0.82):
    candidates = db.query(model_class).filter(
        model_class.dns_sku == None,
        model_class.name != None,
    ).all()
    best_score = 0.0
    best_match = None
    for row in candidates:
        score = _name_similarity(name, row.name or "")
        if score > best_score:
            best_score = score
            best_match = row
    return best_match if best_score >= threshold else None


def _multi_dns_parse(db, queries, model_class, char_mapper, dns_product_to_dict=None,
                     required_fields=None, limit=8):
    total = {"added": 0, "updated": 0, "failed": 0, "skipped": 0}
    for q in queries:
        r = _run_dns_parse(db, q, model_class, char_mapper, dns_product_to_dict,
                           required_fields=required_fields, limit=limit)
        if "error" in r:
            continue
        total["added"] += r.get("added", 0)
        total["updated"] += r.get("updated", 0)
        total["failed"] += r.get("failed", 0)
        total["skipped"] += r.get("skipped", 0)
        time.sleep(1)
    return total


# ── Public API ─────────────────────────────────────────────────────────────────

def parse_mice_dns(db: Session) -> dict:
    queries = [
        "игровая мышь проводная",
        "игровая мышь беспроводная",
        "мышь logitech игровая",
        "мышь razer игровая",
        "мышь steelseries",
    ]
    return _multi_dns_parse(db, queries, Mouse, _map_mouse_dns,
                            required_fields=["sensor", "connection_types"])


def parse_keyboards_dns(db: Session) -> dict:
    queries = [
        "механическая клавиатура игровая",
        "клавиатура logitech механическая",
        "клавиатура razer механическая",
        "беспроводная клавиатура механическая",
    ]
    return _multi_dns_parse(db, queries, Keyboard, _map_keyboard_dns,
                            required_fields=["switches", "connection_types"])


def parse_monitors_dns(db: Session) -> dict:
    queries = [
        "игровой монитор 144hz",
        "монитор 27 дюймов ips",
        "монитор 4k игровой",
    ]
    return _multi_dns_parse(db, queries, Monitor, _map_monitor_dns,
                            required_fields=["matrix_type", "refresh_rate_hz"])


def parse_headphones_dns(db: Session) -> dict:
    queries = [
        "игровые наушники гарнитура",
        "наушники беспроводные игровые",
        "наушники logitech игровые",
    ]
    return _multi_dns_parse(db, queries, Headphones, _map_headphones_dns,
                            required_fields=["construction_type"])


def parse_microphones_dns(db: Session) -> dict:
    queries = [
        "usb микрофон компьютер",
        "конденсаторный микрофон",
    ]
    return _multi_dns_parse(db, queries, Microphone, _map_microphone_dns,
                            required_fields=["mic_type"])


def parse_mousepads_dns(db: Session) -> dict:
    queries = [
        "игровой коврик для мыши",
        "коврик xl для мыши",
    ]
    return _multi_dns_parse(db, queries, Mousepad, _map_mousepad_dns,
                            required_fields=["surface_material"])
