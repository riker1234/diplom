import re
import json
import time
import random
import requests
from difflib import SequenceMatcher
from urllib.parse import quote
from sqlalchemy.orm import Session
from app.models.mouse import Mouse
from app.models.keyboard import Keyboard
from app.models.monitor import Monitor
from app.models.headphones import Headphones
from app.models.microphone import Microphone
from app.models.mousepad import Mousepad

_SEARCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Origin": "https://www.wildberries.ru",
    "Referer": "https://www.wildberries.ru/",
}

# ── Selenium (ленивая инициализация, для поиска WB) ───────────────────────────

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
    driver.get("https://www.wildberries.ru/")
    time.sleep(8)
    _driver = driver
    return _driver


def _browser_search(query: str, limit: int = 50) -> list[dict]:
    """Поиск товаров через JS fetch из контекста браузера WB."""
    driver = _get_driver()
    encoded = quote(query)
    api_url = (
        f"https://www.wildberries.ru/__internal/u-search/exactmatch/ru/common/v18/search"
        f"?ab_testing=false&appType=1&curr=rub&dest=-1257786"
        f"&query={encoded}&resultset=catalog&sort=popular&spp=30"
    )
    result = driver.execute_async_script("""
        var url = arguments[0];
        var cb = arguments[arguments.length - 1];
        fetch(url)
            .then(r => r.json())
            .then(d => cb(d))
            .catch(e => cb({error: e.toString()}))
    """, api_url)
    if not isinstance(result, dict) or "error" in result:
        return []
    # Новый формат WB API (2025+): products на верхнем уровне
    products = result.get("products", []) or result.get("data", {}).get("products", [])
    return products[:limit]

_DETAIL_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://www.wildberries.ru/",
}

# ── Ключи характеристик WB ────────────────────────────────────────────────────

_MOUSE_KEYS = {
    "weight":           {"вес с упаковкой (кг)", "вес мыши", "вес товара без упаковки (г)", "вес", "масса"},
    "connection_types": {"тип подключения мыши", "тип подключения", "интерфейс"},
    "sensor":           {"модель сенсора мыши", "тип датчика мыши", "сенсор", "тип сенсора"},
    "switches":         {"переключатели кнопок мыши", "переключатели", "микровыключатели"},
    "button_count":     {"количество кнопок мыши", "количество кнопок", "кол-во кнопок"},
    "max_dpi":          {"разрешение сенсора мыши", "максимальное разрешение сенсора", "максимальное разрешение"},
    "color":            {"цвет", "цвет товара"},
    "form_factor":      {"хват мыши", "конструкция мыши", "форма"},
    "has_rgb":          {"подсветка мыши", "доп. опции мыши", "подсветка", "rgb подсветка"},
}

_KEYBOARD_KEYS = {
    "keyboard_type":        {"тип клавиатуры"},
    "switches":             {"тип переключателей клавиатуры", "переключатели", "тип переключателей", "модель переключателей клавиатуры", "тип механических переключателей"},
    "form_factor":          {"форм-фактор клавиатуры", "форм-фактор", "конструкция"},
    "board_material":       {"материал корпуса клавиатуры", "материал корпуса"},
    "keycap_material":      {"материал клавиш", "материал кейкапов", "материал колпачков"},
    "keycap_manufacturing": {"способ нанесения символов клавиатуры", "способ нанесения символов", "нанесение символов"},
    "connection_types":     {"тип подключения клавиатуры", "тип подключения", "интерфейс"},
    "has_rgb":              {"подсветка", "rgb подсветка"},
    "layout":               {"раскладка клавиатуры", "раскладка"},
    "key_count":            {"количество клавиш", "кол-во клавиш"},
    "color":                {"цвет товара", "цвет"},
}

_MONITOR_KEYS = {
    "diagonal_inch":    {"диагональ монитора", "диагональ", "размер экрана"},
    "resolution":       {"разрешение экрана", "разрешение"},
    "refresh_rate_hz":  {"частота обновления экрана", "частота обновления", "максимальная частота обновления"},
    "matrix_type":      {"тип матрицы", "тип панели"},
    "response_time_ms": {"время отклика", "время реакции"},
    "brightness_nits":  {"яркость", "максимальная яркость"},
    "hdr":              {"поддержка hdr", "hdr"},
    "color":            {"цвет товара", "цвет"},
}

_HEADPHONES_KEYS = {
    "construction_type":  {"конструкция наушников", "конструкция", "тип конструкции", "вид наушников"},
    "connection_types":   {"тип подключения наушников", "тип подключения", "интерфейс"},
    "extra_options":      {"доп. опции наушников", "особенности наушников"},
    "freq_min":           {"минимальная частота", "мин. частота", "минимальная воспроизводимая частота"},
    "freq_max":           {"максимальная частота", "макс. частота", "максимальная воспроизводимая частота"},
    "impedance_ohm":      {"импеданс", "сопротивление"},
    "color":              {"цвет товара", "цвет"},
}

_MICROPHONE_KEYS = {
    "mic_type":         {"тип микрофона", "тип капсюля"},
    "directionality":   {"направленность микрофона", "направленность", "полярная диаграмма"},
    "connection_types": {"тип подключения микрофона", "тип подключения", "интерфейс"},
    "frequency_range":  {"диапазон частот", "частотный диапазон"},
    "sample_rate":      {"частота дискретизации"},
    "bit_depth":        {"разрядность"},
    "color":            {"цвет товара", "цвет"},
}

_MOUSEPAD_KEYS = {
    "size":             {"размер коврика", "размер", "габариты", "размер коврика для мыши"},
    "surface_material": {"материал поверхности коврика", "материал поверхности", "материал", "покрытие поверхности коврика"},
    "hardness":         {"жёсткость коврика", "жёсткость", "тип поверхности", "тип покрытия коврика"},
    "has_rgb":          {"подсветка коврика", "подсветка", "rgb-подсветка"},
    "color":            {"цвет товара", "цвет"},
    "thickness_mm":     {"толщина", "толщина (мм)", "толщина предмета"},
}


# ── Вспомогательные парсеры ───────────────────────────────────────────────────

def _parse_float(value: str) -> float | None:
    m = re.search(r"[\d]+[.,]?[\d]*", value)
    return float(m.group().replace(",", ".")) if m else None


def _parse_int(value: str) -> int | None:
    # Убираем пробелы между цифрами (русский формат: "7 200" → "7200")
    clean = re.sub(r"(\d)\s+(\d)", r"\1\2", value)
    m = re.search(r"\d+", clean)
    return int(m.group()) if m else None


def _parse_dpi(value: str) -> int | None:
    # Ищем число непосредственно перед словом "dpi"
    m = re.search(r"([\d][\d\s]*)\s*dpi", value, re.IGNORECASE)
    if m:
        return int(re.sub(r"\s+", "", m.group(1)))
    # Запасной вариант: самое большое число в строке (DPI обычно крупнее всех)
    numbers = [int(n) for n in re.findall(r"\d+", re.sub(r"(\d)\s+(\d)", r"\1\2", value))]
    candidates = [n for n in numbers if n >= 400]  # DPI не меньше 400
    return max(candidates) if candidates else None


def _parse_bool(value: str) -> bool:
    low = value.strip().lower()
    return low in ("да", "есть", "yes", "+", "true") or "rgb" in low or "подсветка" in low


def _normalize_connection_type(value: str | None) -> str | None:
    if not value:
        return None
    low = value.lower()
    has_wireless = bool(re.search(r'беспровод|bluetooth|радиоканал', low))
    # Убираем "беспровод*" чтобы слово "провод" внутри не давало ложное срабатывание
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


def _sanitize_sensor(value: str | None) -> str | None:
    """Отбрасывает значения из поля sensor, которые явно не являются названием сенсора."""
    if not value:
        return None
    low = value.lower().strip()
    # Значения, характерные для типа подключения или категории товара
    if re.match(r'(беспровод|провод|игровая|игровой|дистанцион)', low):
        return None
    # DPI-спецификация вместо названия чипа
    if re.match(r'\d[\d\s]*dpi', low, re.IGNORECASE):
        return None
    return value


def _map_options(options: list[dict], keys_map: dict) -> dict:
    result: dict = {k: None for k in keys_map}
    for opt in options:
        name = opt.get("name", "").lower().strip()
        # CDN format: {name, value: str}
        # meta.characteristics format: {name, values: [str, ...]}
        value_raw = opt.get("value") or "; ".join(opt.get("values", []))
        value = str(value_raw).strip()
        for field, key_set in keys_map.items():
            if name in key_set:
                result[field] = value
                break
    return result


# ── Маппер каждой категории ───────────────────────────────────────────────────

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
        "connection_types": _normalize_connection_type(raw.get("connection_types")),
        "sensor":           _sanitize_sensor(raw.get("sensor")),
        "switches":         raw.get("switches"),
        "button_count":     _parse_int(button_str) if button_str else None,
        "max_dpi":          _parse_dpi(max_dpi_str) if max_dpi_str else None,
        "color":            raw.get("color"),
        "form_factor":      raw.get("form_factor"),
        "has_rgb":          _parse_bool(has_rgb_str) if has_rgb_str else False,
    }


def _map_keyboard(options: list[dict]) -> dict:
    raw = _map_options(options, _KEYBOARD_KEYS)
    has_rgb_str = raw.get("has_rgb")
    key_count_str = raw.get("key_count")
    return {
        "keyboard_type":        raw.get("keyboard_type"),
        "switches":             raw.get("switches"),
        "form_factor":          raw.get("form_factor"),
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
    extra = (raw.get("extra_options") or "").lower()
    freq_min = raw.get("freq_min")
    freq_max = raw.get("freq_max")
    if freq_min and freq_max:
        freq_min_val = _parse_int(freq_min)
        freq_max_val = _parse_int(freq_max)
        frequency_response = f"{freq_min_val}-{freq_max_val}" if freq_min_val and freq_max_val else None
    else:
        frequency_response = freq_min or freq_max
    imp_str = raw.get("impedance_ohm")
    # микрофон, шумоподавление и подсветка могут быть в "Доп. опции наушников"
    has_microphone = "микрофон" in extra
    noise_cancellation = "шумоподавление" in extra or None
    has_rgb = "подсветка" in extra or "rgb" in extra
    return {
        "construction_type":  raw.get("construction_type"),
        "connection_types":   _normalize_connection_type(raw.get("connection_types")),
        "has_microphone":     has_microphone,
        "noise_cancellation": "есть" if noise_cancellation else None,
        "frequency_response": frequency_response,
        "impedance_ohm":      _parse_int(imp_str) if imp_str else None,
        "color":              raw.get("color"),
        "has_rgb":            has_rgb,
    }


def _map_microphone(options: list[dict]) -> dict:
    raw = _map_options(options, _MICROPHONE_KEYS)
    return {
        "mic_type":         raw.get("mic_type"),
        "directionality":   raw.get("directionality"),
        "connection_types": _normalize_connection_type(raw.get("connection_types")),
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


# ── WB API: поиск (через Selenium browser context) ───────────────────────────

def _search_wb(query: str, limit: int = 50) -> list[dict]:
    try:
        return _browser_search(query, limit)
    except Exception:
        return []


# ── WB CDN: характеристики через basket-XX.wbbasket.ru ───────────────────────

def _get_basket(vol: int) -> str:
    ranges = [
        (143, "01"), (287, "02"), (431, "03"), (719, "04"),
        (1007, "05"), (1061, "06"), (1115, "07"), (1169, "08"),
        (1313, "09"), (1601, "10"), (1655, "11"), (1919, "12"),
        (2045, "13"), (2189, "14"), (2405, "15"), (2621, "16"),
        (2837, "17"), (3053, "18"), (3269, "19"), (3485, "20"),
        (3701, "21"), (3917, "22"), (4133, "23"), (4349, "24"),
    ]
    for max_vol, basket in ranges:
        if vol <= max_vol:
            return basket
    return "25"


def _build_card_json_url(product_id: int) -> str:
    vol = product_id // 100000
    part = product_id // 1000
    basket = _get_basket(vol)
    return f"https://basket-{basket}.wbbasket.ru/vol{vol}/part{part}/{product_id}/info/ru/card.json"


def _fetch_details(product_ids: list[int]) -> dict[int, list[dict]]:
    result: dict[int, list[dict]] = {}
    for pid in product_ids:
        url = _build_card_json_url(pid)
        try:
            resp = requests.get(url, headers=_DETAIL_HEADERS, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                options = data.get("options", [])
                # card.json может хранить характеристики в grouped_params
                if not options:
                    for group in data.get("grouped_params", []):
                        options.extend(group.get("params", []))
                result[pid] = options
        except Exception:
            pass
        time.sleep(random.uniform(0.2, 0.5))
    return result


# ── Вспомогательные: данные о товаре из поискового ответа ────────────────────

def _get_wb_price(product: dict) -> float | None:
    # Новый формат (2025+): sizes[0].price.product (в копейках *10 → /100 = рубли)
    for size in product.get("sizes", []):
        price_obj = size.get("price", {})
        if isinstance(price_obj, dict):
            val = price_obj.get("product") or price_obj.get("basic")
            if val:
                return round(val / 100, 2)
    # Старый формат: salePriceU / priceU
    sale = product.get("salePriceU") or product.get("priceU")
    if sale:
        return round(sale / 100, 2)
    return None


def _get_wb_url(product: dict) -> str:
    pid = product.get("id", "")
    return f"https://www.wildberries.ru/catalog/{pid}/detail.aspx"


def _name_similarity(a: str, b: str) -> float:
    a = re.sub(r"\s+", " ", a.lower().strip())
    b = re.sub(r"\s+", " ", b.lower().strip())
    return SequenceMatcher(None, a, b).ratio()


def _find_by_name(db, model_class, name: str, threshold: float = 0.82):
    candidates = db.query(model_class).filter(
        model_class.wb_sku == None,
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


# ── Основная логика парсинга ──────────────────────────────────────────────────

def _run_parse(
    db: Session,
    query: str,
    model_class,
    char_mapper,
    limit: int = 8,
    required_fields: list[str] | None = None,
) -> dict:
    added = updated = failed = skipped = 0

    try:
        products = _search_wb(query, limit)
    except Exception as e:
        return {"added": 0, "updated": 0, "failed": 0, "skipped": 0, "error": str(e)}

    if not products:
        return {"added": 0, "updated": 0, "failed": 0, "skipped": 0}

    details = _fetch_details([p["id"] for p in products])

    # meta.characteristics из поискового ответа — запасной источник
    meta_chars: dict[int, list[dict]] = {}
    for p in products:
        chars = p.get("meta", {}).get("characteristics", [])
        if chars:
            meta_chars[p["id"]] = chars

    for product in products:
        try:
            pid = product.get("id")
            if not pid:
                continue
            wb_sku = str(pid)
            name = product.get("name", "")
            brand = product.get("brand", "")
            wb_price = _get_wb_price(product)
            wb_url = _get_wb_url(product)
            image_url = None
            # Фото: https://basket-XX.wbbasket.ru/vol{vol}/part{part}/{id}/images/big/1.webp
            try:
                vol = pid // 100000
                part = pid // 1000
                basket = _get_basket(vol)
                image_url = f"https://basket-{basket}.wbbasket.ru/vol{vol}/part{part}/{pid}/images/big/1.webp"
            except Exception:
                pass

            cdn_opts = details.get(pid, [])
            meta_opts = meta_chars.get(pid, [])
            # Объединяем: CDN даёт больше полей, meta — основные
            combined_opts = cdn_opts if cdn_opts else meta_opts
            chars = char_mapper(combined_opts)

            # Уже есть по WB SKU — обновляем цену
            existing = db.query(model_class).filter(model_class.wb_sku == wb_sku).first()
            if existing:
                existing.wb_price = wb_price
                if image_url and not existing.image_url:
                    existing.image_url = image_url
                for field, value in chars.items():
                    if value is not None:
                        setattr(existing, field, value)
                db.commit()
                updated += 1
                continue

            # Ищем по названию среди Ozon-записей без WB
            matched = _find_by_name(db, model_class, name)
            if matched:
                matched.wb_sku = wb_sku
                matched.wb_url = wb_url
                matched.wb_price = wb_price
                if image_url and not matched.image_url:
                    matched.image_url = image_url
                for field, value in chars.items():
                    if value is not None:
                        setattr(matched, field, value)
                db.commit()
                updated += 1
            else:
                # Новый товар только с WB
                if required_fields and all(chars.get(f) is None for f in required_fields):
                    skipped += 1
                    continue
                db.add(model_class(
                    name=name,
                    brand=brand or None,
                    wb_sku=wb_sku,
                    wb_url=wb_url,
                    wb_price=wb_price,
                    image_url=image_url,
                    **chars,
                ))
                db.commit()
                added += 1
        except Exception:
            failed += 1
            db.rollback()

    return {"added": added, "updated": updated, "failed": failed, "skipped": skipped}


def _multi_parse(
    db: Session,
    queries: list[str],
    model_class,
    char_mapper,
    limit: int = 8,
    required_fields: list[str] | None = None,
) -> dict:
    total = {"added": 0, "updated": 0, "failed": 0, "skipped": 0}
    for q in queries:
        r = _run_parse(db, q, model_class, char_mapper, limit=limit, required_fields=required_fields)
        if "error" in r:
            continue
        total["added"] += r.get("added", 0)
        total["updated"] += r.get("updated", 0)
        total["failed"] += r.get("failed", 0)
        total["skipped"] += r.get("skipped", 0)
        time.sleep(1)
    return total


# ── Публичный API ─────────────────────────────────────────────────────────────

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


def parse_keyboards(db: Session) -> dict:
    queries = [
        "механическая клавиатура игровая",
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
        "монитор curved изогнутый игровой",
    ]
    return _multi_parse(db, queries, Monitor, _map_monitor, required_fields=["matrix_type", "refresh_rate_hz"])


def parse_headphones(db: Session) -> dict:
    queries = [
        "игровые наушники гарнитура",
        "наушники беспроводные игровые",
        "наушники logitech игровые",
        "наушники razer gaming",
        "игровые наушники rgb",
    ]
    return _multi_parse(db, queries, Headphones, _map_headphones, required_fields=["construction_type"])


def parse_microphones(db: Session) -> dict:
    queries = [
        "usb микрофон компьютер",
        "конденсаторный микрофон usb",
        "микрофон стриминговый",
        "микрофон hyperx",
    ]
    return _multi_parse(db, queries, Microphone, _map_microphone, required_fields=["mic_type"])


def parse_mousepads(db: Session) -> dict:
    queries = [
        "игровой коврик для мыши",
        "коврик xl большой мыши",
        "коврик для мыши rgb",
        "коврик logitech игровой",
        "коврик steelseries xl",
    ]
    return _multi_parse(db, queries, Mousepad, _map_mousepad, required_fields=["surface_material"])
