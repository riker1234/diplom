import re
import time
import random
from difflib import SequenceMatcher
from sqlalchemy.orm import Session
from app.models.mouse import Mouse
from app.models.keyboard import Keyboard
from app.models.monitor import Monitor
from app.models.headphones import Headphones
from app.models.microphone import Microphone
from app.models.mousepad import Mousepad

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
    driver.get("https://www.citilink.ru/")
    time.sleep(5)
    _driver = driver
    return _driver


# ── Поиск: получаем список товаров со страницы поиска ────────────────────────

def _search_citilink(query: str, limit: int = 36) -> list[dict]:
    driver = _get_driver()
    from urllib.parse import quote
    url = f"https://www.citilink.ru/search/?text={quote(query)}"
    driver.get(url)
    time.sleep(5)
    cards = driver.execute_script("""
        var cards = document.querySelectorAll('[data-meta-product-id]');
        var result = [];
        for (var i = 0; i < cards.length; i++) {
            var c = cards[i];
            var a = c.querySelector('a[href*="/product/"]');
            // Ищем название по нескольким вариантам классов
            var nameSelectors = [
                '[class*="title"]', '[class*="Title"]',
                '[class*="name"]', '[class*="Name"]',
                'a[href*="/product/"]'
            ];
            var name = '';
            for (var s = 0; s < nameSelectors.length; s++) {
                var el = c.querySelector(nameSelectors[s]);
                if (el && el.innerText && el.innerText.trim().length > 5) {
                    name = el.innerText.trim().split('\\n')[0];
                    break;
                }
            }
            result.push({
                id: c.getAttribute('data-meta-product-id'),
                href: a ? a.href : '',
                name: name
            });
        }
        return result;
    """)
    seen = set()
    unique = []
    for c in (cards or []):
        pid = c.get("id")
        if pid and pid not in seen and c.get("href"):
            seen.add(pid)
            unique.append(c)
    return unique[:limit]


# ── Характеристики: открываем /properties/ в Selenium ────────────────────────

def _get_properties(product_url: str) -> tuple[dict, float | None]:
    """Возвращает (словарь характеристик, цена)."""
    driver = _get_driver()
    props_url = product_url.rstrip("/") + "/properties/"
    driver.get(props_url)
    time.sleep(4)

    data = driver.execute_script("""
        var result = {};
        var items = document.querySelectorAll('[class*="Properties"]');
        items.forEach(function(el) {
            var children = el.children;
            if (children.length >= 2) {
                var name = children[0].innerText.trim().replace(/:$/, '');
                var val  = children[1].innerText.trim();
                if (name && val && name.length < 80 && !result[name]) {
                    result[name] = val;
                }
            }
        });
        return result;
    """)

    price_raw = driver.execute_script("""
        var selectors = [
            '[class*="Price__price"]',
            '[class*="price__price"]',
            '[data-meta-name="Price"]',
            '[class*="ProductHeader__price"]',
            '[class*="productHeader__price"]',
        ];
        for (var i = 0; i < selectors.length; i++) {
            var el = document.querySelector(selectors[i]);
            if (el && el.innerText.trim()) return el.innerText.trim();
        }
        // Ищем любой элемент с ₽
        var all = document.querySelectorAll('*');
        for (var i = 0; i < all.length; i++) {
            var t = all[i].childNodes;
            for (var j = 0; j < t.length; j++) {
                if (t[j].nodeType === 3 && t[j].textContent.includes('₽')) {
                    var txt = t[j].textContent.trim();
                    if (/^\\d[\\d\\s]*₽/.test(txt)) return txt;
                }
            }
        }
        return null;
    """)
    price = None
    if price_raw:
        m = re.search(r"[\d\s]+", price_raw.replace("\xa0", ""))
        if m:
            price = float(re.sub(r"\s+", "", m.group()))

    return (data or {}, price)


# ── Вспомогательные парсеры ───────────────────────────────────────────────────

def _parse_int(value: str) -> int | None:
    clean = re.sub(r"(\d)\s+(\d)", r"\1\2", value)
    m = re.search(r"\d+", clean)
    return int(m.group()) if m else None


def _parse_float(value: str) -> float | None:
    m = re.search(r"[\d]+[.,]?[\d]*", value)
    return float(m.group().replace(",", ".")) if m else None


def _parse_bool(value: str) -> bool:
    low = value.strip().lower()
    return low in ("да", "есть", "yes", "+", "true") or "rgb" in low or "подсветка" in low


def _get(props: dict, *keys: str) -> str | None:
    for k in keys:
        v = props.get(k)
        if v:
            return v
    return None


# ── Маппер: мышь ─────────────────────────────────────────────────────────────

def _map_mouse(props: dict) -> dict:
    weight_str = _get(props, "Вес")
    weight_g = None
    if weight_str:
        val = _parse_float(weight_str)
        if val is not None:
            weight_g = round(val * 1000) if val < 10 else val

    max_dpi_str = _get(props, "Разрешение сенсора, макс.", "Разрешение сенсора")
    max_dpi = None
    if max_dpi_str:
        m = re.search(r"([\d][\d\s]*)\s*dpi", max_dpi_str, re.IGNORECASE)
        if m:
            max_dpi = int(re.sub(r"\s+", "", m.group(1)))
        else:
            max_dpi = _parse_int(max_dpi_str)

    has_rgb_str = _get(props, "Подсветка", "Тип подсветки")
    return {
        "brand":            _get(props, "Бренд"),
        "connection_types": _get(props, "Тип соединения мыши", "Интерфейс подключения"),
        "sensor":           _get(props, "Сенсор"),
        "switches":         _get(props, "Переключатели кнопок"),
        "button_count":     _parse_int(_get(props, "Количество кнопок") or ""),
        "max_dpi":          max_dpi,
        "weight_g":         weight_g,
        "color":            _get(props, "Цвет"),
        "form_factor":      _get(props, "Хват", "Дизайн"),
        "has_rgb":          _parse_bool(has_rgb_str) if has_rgb_str else False,
    }


# ── Маппер: клавиатура ────────────────────────────────────────────────────────

def _map_keyboard(props: dict) -> dict:
    has_rgb_str = _get(props, "Подсветка", "Тип подсветки")
    key_count_str = _get(props, "Количество клавиш")
    return {
        "brand":                _get(props, "Бренд"),
        "switches":             _get(props, "Тип переключателей", "Переключатели"),
        "form_factor":          _get(props, "Форм-фактор", "Конструкция"),
        "board_material":       _get(props, "Материал корпуса"),
        "keycap_material":      _get(props, "Материал клавиш", "Материал кейкапов"),
        "keycap_manufacturing": _get(props, "Способ нанесения символов", "Нанесение символов"),
        "connection_types":     _get(props, "Тип подключения", "Интерфейс подключения"),
        "layout":               _get(props, "Раскладка"),
        "key_count":            _parse_int(key_count_str) if key_count_str else None,
        "color":                _get(props, "Цвет"),
        "has_rgb":              _parse_bool(has_rgb_str) if has_rgb_str else False,
    }


# ── Маппер: монитор ───────────────────────────────────────────────────────────

def _map_monitor(props: dict) -> dict:
    diag_str = _get(props, "Диагональ экрана", "Диагональ")
    refresh_str = _get(props, "Частота обновления экрана", "Частота обновления", "Максимальная частота обновления")
    resp_str = _get(props, "Время отклика")
    bright_str = _get(props, "Яркость", "Максимальная яркость")
    hdr_str = _get(props, "Поддержка HDR", "HDR")
    return {
        "brand":            _get(props, "Бренд"),
        "diagonal_inch":    _parse_float(diag_str) if diag_str else None,
        "resolution":       _get(props, "Разрешение экрана", "Разрешение"),
        "refresh_rate_hz":  _parse_int(refresh_str) if refresh_str else None,
        "matrix_type":      _get(props, "Тип матрицы", "Тип панели"),
        "response_time_ms": _parse_float(resp_str) if resp_str else None,
        "brightness_nits":  _parse_int(bright_str) if bright_str else None,
        "hdr":              _parse_bool(hdr_str) if hdr_str else False,
        "color":            _get(props, "Цвет"),
    }


# ── Маппер: наушники ──────────────────────────────────────────────────────────

def _map_headphones(props: dict) -> dict:
    freq_min_str = _get(props, "Минимальная воспроизводимая частота", "Минимальная частота")
    freq_max_str = _get(props, "Максимальная воспроизводимая частота", "Максимальная частота")
    frequency_response = None
    if freq_min_str and freq_max_str:
        fmin = _parse_int(freq_min_str)
        fmax = _parse_int(freq_max_str)
        if fmin and fmax:
            frequency_response = f"{fmin}-{fmax}"
    imp_str = _get(props, "Импеданс", "Сопротивление")
    has_mic_str = _get(props, "Микрофон", "Встроенный микрофон")
    has_rgb_str = _get(props, "Подсветка", "Тип подсветки")
    noise_str = _get(props, "Шумоподавление", "Активное шумоподавление")
    return {
        "brand":             _get(props, "Бренд"),
        "construction_type": _get(props, "Вид наушников", "Конструкция", "Тип наушников"),
        "connection_types":  _get(props, "Тип подключения", "Интерфейс подключения"),
        "has_microphone":    _parse_bool(has_mic_str) if has_mic_str else False,
        "noise_cancellation": "есть" if noise_str and _parse_bool(noise_str) else None,
        "frequency_response": frequency_response,
        "impedance_ohm":     _parse_int(imp_str) if imp_str else None,
        "color":             _get(props, "Цвет"),
        "has_rgb":           _parse_bool(has_rgb_str) if has_rgb_str else False,
    }


# ── Маппер: микрофон ──────────────────────────────────────────────────────────

def _map_microphone(props: dict) -> dict:
    freq_str = _get(props, "Диапазон частот", "Частотный диапазон")
    return {
        "brand":            _get(props, "Бренд"),
        "mic_type":         _get(props, "Тип микрофона", "Тип капсюля"),
        "directionality":   _get(props, "Направленность", "Полярная диаграмма"),
        "connection_types": _get(props, "Тип подключения", "Интерфейс подключения"),
        "frequency_range":  freq_str,
        "sample_rate":      _get(props, "Частота дискретизации"),
        "bit_depth":        _get(props, "Разрядность"),
        "color":            _get(props, "Цвет"),
    }


# ── Маппер: коврик ────────────────────────────────────────────────────────────

def _map_mousepad(props: dict) -> dict:
    thickness_str = _get(props, "Толщина", "Толщина коврика")
    has_rgb_str = _get(props, "Подсветка")
    return {
        "brand":            _get(props, "Бренд"),
        "size":             _get(props, "Размер коврика", "Размер"),
        "surface_material": _get(props, "Материал поверхности", "Покрытие поверхности"),
        "hardness":         _get(props, "Жёсткость", "Тип поверхности"),
        "color":            _get(props, "Цвет"),
        "thickness_mm":     _parse_float(thickness_str) if thickness_str else None,
        "has_rgb":          _parse_bool(has_rgb_str) if has_rgb_str else False,
    }


# ── Матчинг по названию ───────────────────────────────────────────────────────

def _name_similarity(a: str, b: str) -> float:
    a = re.sub(r"\s+", " ", a.lower().strip())
    b = re.sub(r"\s+", " ", b.lower().strip())
    return SequenceMatcher(None, a, b).ratio()


def _find_by_name(db, model_class, name: str, threshold: float = 0.82):
    candidates = db.query(model_class).filter(
        model_class.citilink_sku == None,
        model_class.name != None,
    ).all()
    best_score, best_match = 0.0, None
    for row in candidates:
        score = _name_similarity(name, row.name or "")
        if score > best_score:
            best_score = score
            best_match = row
    return best_match if best_score >= threshold else None


# ── Основная логика ───────────────────────────────────────────────────────────

def _run_parse(
    db: Session,
    queries: list[str],
    model_class,
    char_mapper,
    required_fields: list[str] | None = None,
) -> dict:
    added = updated = failed = skipped = 0
    seen_ids: set[str] = set()

    for query in queries:
        try:
            products = _search_citilink(query, limit=36)
        except Exception as e:
            continue

        for product in products:
            try:
                citilink_sku = product.get("id")
                if not citilink_sku or citilink_sku in seen_ids:
                    continue
                seen_ids.add(citilink_sku)

                href = product.get("href", "")
                if not href:
                    continue

                # Убираем /properties/ если случайно попало
                base_url = re.sub(r"/properties/?$", "", href).rstrip("/") + "/"
                citilink_url = base_url

                props, citilink_price = _get_properties(base_url)
                if not props:
                    skipped += 1
                    continue

                chars = char_mapper(props)
                name = product.get("name") or ""
                if not name:
                    # Берём из заголовка страницы если карточка не дала названия
                    name = _get_driver().execute_script(
                        "var h = document.querySelector('h1'); return h ? h.innerText : '';"
                    ) or citilink_sku
                brand = chars.pop("brand", None)

                if required_fields and all(chars.get(f) is None for f in required_fields):
                    skipped += 1
                    continue

                # Проверяем — уже есть по SKU
                existing = db.query(model_class).filter(
                    model_class.citilink_sku == citilink_sku
                ).first()
                if existing:
                    existing.citilink_price = citilink_price
                    for f, v in chars.items():
                        if v is not None:
                            setattr(existing, f, v)
                    db.commit()
                    updated += 1
                    continue

                # Ищем по названию среди уже существующих записей
                matched = _find_by_name(db, model_class, name)
                if matched:
                    matched.citilink_sku = citilink_sku
                    matched.citilink_url = citilink_url
                    matched.citilink_price = citilink_price
                    for f, v in chars.items():
                        if v is not None:
                            setattr(matched, f, v)
                    db.commit()
                    updated += 1
                else:
                    db.add(model_class(
                        name=name,
                        brand=brand,
                        price=citilink_price,
                        citilink_sku=citilink_sku,
                        citilink_url=citilink_url,
                        citilink_price=citilink_price,
                        **chars,
                    ))
                    db.commit()
                    added += 1

                time.sleep(random.uniform(0.5, 1.2))

            except Exception:
                failed += 1
                db.rollback()

        time.sleep(2)

    return {"added": added, "updated": updated, "failed": failed, "skipped": skipped}


# ── Публичные функции парсинга ────────────────────────────────────────────────

def parse_mice(db: Session) -> dict:
    return _run_parse(db, [
        "игровая мышь", "мышь logitech игровая", "мышь razer",
        "мышь беспроводная игровая", "мышь steelseries",
    ], Mouse, _map_mouse, required_fields=["connection_types"])


def parse_keyboards(db: Session) -> dict:
    return _run_parse(db, [
        "механическая клавиатура", "клавиатура logitech механическая",
        "клавиатура razer механическая", "клавиатура игровая rgb",
    ], Keyboard, _map_keyboard, required_fields=["switches"])


def parse_monitors(db: Session) -> dict:
    return _run_parse(db, [
        "игровой монитор 144hz", "монитор 27 дюймов ips",
        "монитор 240hz gaming", "монитор 4k",
    ], Monitor, _map_monitor, required_fields=["matrix_type"])


def parse_headphones(db: Session) -> dict:
    return _run_parse(db, [
        "игровые наушники гарнитура", "наушники беспроводные gaming",
        "наушники logitech игровые",
    ], Headphones, _map_headphones, required_fields=["construction_type"])


def parse_microphones(db: Session) -> dict:
    return _run_parse(db, [
        "usb микрофон конденсаторный", "микрофон стриминговый",
        "микрофон hyperx",
    ], Microphone, _map_microphone, required_fields=["mic_type"])


def parse_mousepads(db: Session) -> dict:
    return _run_parse(db, [
        "игровой коврик для мыши xl", "коврик rgb игровой",
        "коврик logitech steelseries",
    ], Mousepad, _map_mousepad, required_fields=["surface_material"])
