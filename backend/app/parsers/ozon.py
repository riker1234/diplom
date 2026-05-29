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
    time.sleep(10)
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
    "weight":           {"вес", "вес товара", "вес с упаковкой", "вес устройства", "масса",
                         "вес мыши", "вес товара без упаковки (г)", "вес нетто"},
    "connection_types": {"тип соединения", "тип подключения", "интерфейс подключения",
                         "тип соединения мыши", "тип подключения мыши", "интерфейс",
                         "тип беспроводного соединения", "подключение"},
    "sensor":           {"тип датчика", "модель сенсора", "тип сенсора", "сенсор",
                         "сенсор мыши", "датчик", "технология датчика"},
    "switches":         {"тип переключателей", "переключатели", "микровыключатели",
                         "переключатели кнопок мыши", "переключатели кнопок"},
    "button_count":     {"количество кнопок", "кол-во кнопок", "количество кнопок мыши",
                         "число кнопок"},
    "max_dpi":          {"макс. разрешение датчика, dpi", "максимальное разрешение",
                         "разрешение датчика", "макс. dpi", "dpi", "максимальное dpi",
                         "разрешение сенсора, макс."},
    "color":            {"цвет", "цвет товара"},
    "form_factor":      {"форма", "конструкция мыши", "хват мыши", "конструкция"},
    "has_rgb":          {"подсветка", "rgb подсветка", "rgb-подсветка",
                         "подсветка мыши", "доп. опции мыши"},
}

_KEYBOARD_KEYS = {
    "keyboard_type":        {"тип клавиатуры", "тип устройства"},
    "switches":             {"тип переключателей", "переключатели", "тип свитчей",
                             "тип механических клавиш", "тип механических переключателей",
                             "тип переключателей клавиатуры", "модель переключателей клавиатуры",
                             "переключатели клавиш"},
    "form_factor":          {"форм-фактор", "размер клавиатуры", "конструкция", "форма",
                             "форм-фактор клавиатуры", "компоновка", "размер"},
    "board_material":       {"материал корпуса", "основной материал корпуса",
                             "материал корпуса клавиатуры"},
    "keycap_material":      {"материал клавиш", "материал кейкапов", "материал колпачков"},
    "keycap_manufacturing": {"способ нанесения символов", "нанесение символов",
                             "способ нанесения символов клавиатуры"},
    "connection_types":     {"тип подключения", "интерфейс", "тип соединения",
                             "тип подключения клавиатуры", "подключение", "интерфейс подключения"},
    "has_rgb":              {"подсветка", "rgb подсветка", "rgb-подсветка",
                             "подсветка клавиатуры", "тип подсветки"},
    "layout":               {"раскладка клавиатуры", "раскладка", "языковая раскладка",
                             "язык", "язык раскладки"},
    "key_count":            {"количество клавиш", "кол-во клавиш", "число клавиш"},
    "color":                {"цвет", "цвет товара"},
}

_MONITOR_KEYS = {
    "diagonal_inch":    {"диагональ экрана, дюймы", "диагональ экрана", "диагональ",
                         "размер экрана", "размер экрана, дюймы", "диагональ монитора"},
    "resolution":       {"разрешение экрана", "разрешение", "разрешение матрицы"},
    "refresh_rate_hz":  {"макс. частота обновления, гц", "частота обновления экрана",
                         "частота обновления", "максимальная частота обновления",
                         "частота обновления экрана монитора", "частота кадров"},
    "matrix_type":      {"матрица монитора", "тип матрицы", "тип панели",
                         "технология матрицы", "тип экрана"},
    "response_time_ms": {"время отклика, мс", "время отклика", "время реакции",
                         "время отклика матрицы"},
    "brightness_nits":  {"яркость, кд/м2", "яркость", "максимальная яркость",
                         "яркость экрана"},
    "hdr":              {"технология hdr", "hdr", "поддержка hdr", "hdr поддержка"},
    "color":            {"цвет", "цвет товара"},
}

_HEADPHONES_KEYS = {
    "construction_type":  {"конструкция", "тип конструкции", "конструкция наушников",
                           "вид наушников", "тип наушников", "форм-фактор"},
    "connection_types":   {"тип подключения", "интерфейс", "подключение",
                           "тип беспроводной связи", "тип соединения", "интерфейс подключения"},
    "has_microphone":     {"наличие микрофона", "микрофон", "встроенный микрофон",
                           "микрофон в комплекте"},
    "noise_cancellation": {"шумоподавление", "активное шумоподавление", "анр",
                           "noise cancelling", "подавление шума"},
    "freq_min":           {"мин. частота, гц", "минимальная частота",
                           "нижняя граница частотного диапазона"},
    "freq_max":           {"макс. частота, гц", "максимальная частота",
                           "верхняя граница частотного диапазона"},
    "impedance_ohm":      {"импеданс, ом", "импеданс", "сопротивление", "сопротивление, ом"},
    "color":              {"цвет", "цвет товара"},
    "has_rgb":            {"подсветка", "rgb подсветка", "rgb-подсветка"},
}

_MICROPHONE_KEYS = {
    "mic_type":         {"технология микрофона", "тип микрофона", "тип капсюля",
                         "тип микрофонного капсюля", "принцип действия"},
    "directionality":   {"диаграмма направленности", "направленность", "полярная диаграмма",
                         "характеристика направленности", "паттерн направленности"},
    "connection_types": {"интерфейсы и разъемы", "тип подключения", "интерфейс",
                         "разъём", "тип разъёма", "подключение"},
    "frequency_range":  {"диапазон частот", "частотный диапазон", "диапазон воспроизводимых частот"},
    "sample_rate":      {"частота дискретизации", "частота дискретизации звука",
                         "частота семплирования"},
    "bit_depth":        {"разрядность", "разрядность звука", "битрейт", "глубина бит"},
    "color":            {"цвет", "цвет товара"},
}

_MOUSEPAD_KEYS = {
    "size":             {"размер", "габариты", "размер коврика", "габариты коврика",
                         "длина x ширина"},
    "surface_material": {"материал поверхности", "материал", "материал покрытия",
                         "тип поверхности", "покрытие"},
    "hardness":         {"жёсткость", "тип поверхности", "характеристика покрытия",
                         "жёсткость поверхности", "тип коврика"},
    "has_rgb":          {"подсветка", "rgb-подсветка", "rgb подсветка",
                         "подсветка коврика"},
    "color":            {"цвет", "цвет товара"},
    "thickness_mm":     {"толщина, мм", "толщина", "толщина коврика"},
}


def _normalize_connection_type(value: str | None) -> str | None:
    if not value:
        return None
    low = value.lower()
    has_wireless = bool(re.search(r'беспровод|bluetooth|радиоканал', low))
    cleaned = re.sub(r'беспровод\w*', '', low)
    has_wired = bool(re.search(r'провод', cleaned)) or (
        bool(re.search(r'\busb\b', cleaned)) and 'донгл' not in cleaned
    )
    if has_wired and has_wireless:
        return "проводная/беспроводная"
    if has_wireless:
        return "беспроводная"
    if has_wired:
        return "проводная"
    return value


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


def _normalize_form_factor(value: str | None, name: str = "") -> str | None:
    if value and value.lower() not in ("универсальная", "универсальный", "стандартная"):
        return value
    text = (name + " " + (value or "")).lower()
    if "tkl" in text or "tenkeyless" in text or "без цифрового" in text:
        return "TKL"
    for pct in ("60%", "65%", "75%", "80%", "96%"):
        if pct in text:
            return pct
    if "full" in text or "полноразмер" in text:
        return "Full"
    return value


def _map_keyboard(options: list[dict], name: str = "") -> dict:
    raw = _map_options(options, _KEYBOARD_KEYS)
    has_rgb_str = raw.get("has_rgb")
    key_count_str = raw.get("key_count")
    return {
        "keyboard_type":        raw.get("keyboard_type"),
        "switches":             raw.get("switches"),
        "form_factor":          _normalize_form_factor(raw.get("form_factor"), name),
        "board_material":       raw.get("board_material"),
        "keycap_material":      raw.get("keycap_material"),
        "keycap_manufacturing": raw.get("keycap_manufacturing"),
        "connection_types":     _normalize_connection_type(raw.get("connection_types")),
        "has_rgb":              _parse_bool(has_rgb_str) if has_rgb_str else False,
        "layout":               raw.get("layout"),
        "key_count":            _parse_int(key_count_str) if key_count_str else None,
        "color":                raw.get("color"),
    }


def _map_monitor(options: list[dict]) -> dict:
    raw = _map_options(options, _MONITOR_KEYS)
    hdr_str = raw.get("hdr")
    brightness_str = raw.get("brightness_nits")
    response_str = raw.get("response_time_ms")
    return {
        "diagonal_inch":    _parse_float(raw["diagonal_inch"])   if raw["diagonal_inch"]   else None,
        "resolution":       raw["resolution"],
        "refresh_rate_hz":  _parse_int(raw["refresh_rate_hz"])   if raw["refresh_rate_hz"] else None,
        "matrix_type":      raw["matrix_type"],
        "response_time_ms": _parse_float(response_str) if response_str else None,
        "brightness_nits":  _parse_int(brightness_str) if brightness_str else None,
        "hdr":              _parse_bool(hdr_str) if hdr_str else False,
        "color":            raw.get("color"),
    }


def _map_headphones(options: list[dict]) -> dict:
    raw = _map_options(options, _HEADPHONES_KEYS)
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
        "has_microphone":     _parse_bool(has_mic_str) if has_mic_str else False,
        "noise_cancellation": raw.get("noise_cancellation"),
        "frequency_response": frequency_response,
        "impedance_ohm":      _parse_int(imp_str) if imp_str else None,
        "color":              raw.get("color"),
        "has_rgb":            _parse_bool(has_rgb_str) if has_rgb_str else False,
    }


def _map_microphone(options: list[dict]) -> dict:
    raw = _map_options(options, _MICROPHONE_KEYS)
    return {
        "mic_type":         raw.get("mic_type"),
        "directionality":   raw.get("directionality"),
        "connection_types": raw.get("connection_types"),
        "frequency_range":  raw.get("frequency_range"),
        "sample_rate":      raw.get("sample_rate"),
        "bit_depth":        raw.get("bit_depth"),
        "color":            raw.get("color"),
    }


def _map_mousepad(options: list[dict]) -> dict:
    raw = _map_options(options, _MOUSEPAD_KEYS)
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


def _get_brand(product: dict, name: str = "") -> str:
    for state in product.get("mainState", []):
        if state.get("type") == "labelListV2":
            items = state.get("labelListV2", {}).get("items", [])
            for item in items:
                if item.get("type") == "text":
                    text = item.get("text", {}).get("text", "").strip()
                    if text and not re.match(r"^\d+(\.\d+)?$", text):
                        return text
    # Fallback: first word of product name
    if name:
        first = name.strip().split()[0]
        if len(first) > 1 and not re.match(r"^\d+$", first):
            return first
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


def _run_parse(
    db: Session,
    query: str,
    model_class,
    char_mapper,
    limit: int = 8,
    required_fields: list[str] | None = None,
    exclude_name_kw: list[str] | None = None,
) -> dict:
    added = updated = failed = skipped = 0
    try:
        products, details = _fetch_all(query, limit)
    except Exception as e:
        return {"added": 0, "updated": 0, "failed": 0, "skipped": 0, "error": str(e)}

    if not products:
        return {"added": 0, "updated": 0, "failed": 0, "skipped": 0}

    for product in products:
        try:
            pid = product.get("id")
            if not pid:
                continue
            ozon_sku = str(pid)
            name = _get_name(product)
            if exclude_name_kw and any(kw.lower() in (name or "").lower() for kw in exclude_name_kw):
                skipped += 1
                continue
            brand = _get_brand(product, name)
            price = _get_price(product)
            image_url = _get_image(product)
            product_url = _get_url(product)
            ozon_url = f"https://www.ozon.ru{product_url}" if product_url.startswith("/") else product_url

            raw_chars = details.get(str(pid), [])
            try:
                chars = char_mapper(raw_chars, name)
            except TypeError:
                chars = char_mapper(raw_chars)

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
                if required_fields and all(chars.get(f) is None for f in required_fields):
                    skipped += 1
                    continue
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

    return {"added": added, "updated": updated, "failed": failed, "skipped": skipped}


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
    return _multi_parse(db, queries, Mouse, _map_mouse, required_fields=["sensor", "connection_types"])

def _multi_parse(
    db: Session,
    queries: list[str],
    model_class,
    char_mapper,
    limit: int = 8,
    required_fields: list[str] | None = None,
    exclude_name_kw: list[str] | None = None,
) -> dict:
    total = {"added": 0, "updated": 0, "failed": 0, "skipped": 0}
    for q in queries:
        r = _run_parse(db, q, model_class, char_mapper, limit=limit, required_fields=required_fields, exclude_name_kw=exclude_name_kw)
        if "error" in r:
            continue
        total["added"] += r.get("added", 0)
        total["updated"] += r.get("updated", 0)
        total["failed"] += r.get("failed", 0)
        total["skipped"] += r.get("skipped", 0)
        time.sleep(1)
    return total


def parse_keyboards(db: Session) -> dict:
    queries = [
        "механическая клавиатура игровая",
        "клавиатура механическая cherry mx",
        "клавиатура logitech механическая",
        "клавиатура razer механическая",
        "клавиатура full size механическая",
        "клавиатура tkl механическая rgb",
        "беспроводная клавиатура механическая",
    ]
    return _multi_parse(db, queries, Keyboard, _map_keyboard, required_fields=["switches", "connection_types"])


def parse_monitors(db: Session) -> dict:
    queries = [
        "игровой монитор 144hz",
        "игровой монитор 240hz",
        "монитор 27 дюймов ips",
        "монитор 24 дюйма gaming",
        "монитор 4k игровой",
        "монитор для игр 1ms",
        "монитор curved изогнутый игровой",
    ]
    return _multi_parse(db, queries, Monitor, _map_monitor, required_fields=["matrix_type", "refresh_rate_hz"])


def parse_headphones(db: Session) -> dict:
    queries = [
        "игровые наушники гарнитура",
        "наушники беспроводные игровые",
        "гарнитура с микрофоном gaming",
        "наушники logitech игровые",
        "наушники razer gaming",
        "наушники steelseries игровые",
        "игровые наушники rgb",
    ]
    return _multi_parse(db, queries, Headphones, _map_headphones, required_fields=["construction_type"])


def parse_microphones(db: Session) -> dict:
    queries = [
        "usb микрофон компьютер",
        "конденсаторный микрофон usb",
        "микрофон стриминговый",
        "микрофон для подкаста",
        "микрофон hyperx",
        "микрофон rode стриминг",
        "микрофон blue yeti",
    ]
    return _multi_parse(db, queries, Microphone, _map_microphone, required_fields=["mic_type"],
                        exclude_name_kw=["съёмный", "сменный", "для гарнитур", "для наушник"])


def parse_mousepads(db: Session) -> dict:
    queries = [
        "игровой коврик для мыши",
        "коврик xl большой мыши",
        "коврик для мыши rgb",
        "коврик logitech игровой",
        "коврик steelseries xl",
        "коврик razer игровой",
        "коврик для мыши скоростной",
    ]
    return _multi_parse(db, queries, Mousepad, _map_mousepad, required_fields=["surface_material"])


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
