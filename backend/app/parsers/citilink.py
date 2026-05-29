import re
import time
import random
import logging
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

logger = logging.getLogger(__name__)

_page_lock = threading.Lock()
_citi_ctx = None
_citi_page = None


def _get_citi_page():
    global _citi_ctx, _citi_page
    with _page_lock:
        if _citi_page is not None:
            try:
                _ = _citi_page.url
                return _citi_page
            except Exception:
                pass
        logger.info("citilink: creating new browser context...")
        _citi_ctx = new_context()
        _citi_page = _citi_ctx.new_page()
        logger.info("citilink: navigating to homepage...")
        try:
            _citi_page.goto("https://www.citilink.ru/", wait_until="load", timeout=30000)
            logger.info("citilink: homepage loaded")
        except Exception as e:
            logger.warning("citilink: homepage load error (continuing): %s", e)
    return _citi_page


def _reset_citi_page():
    """Close and recreate the browser context (resets DNS cache and cookies)."""
    global _citi_ctx, _citi_page
    with _page_lock:
        try:
            if _citi_ctx:
                _citi_ctx.close()
        except Exception:
            pass
        _citi_ctx = None
        _citi_page = None
    logger.info("citilink: browser context reset, sleeping 30s before retry...")
    time.sleep(30)
    return _get_citi_page()


# ── Поиск: список товаров со страницы поиска ─────────────────────────────────

def _search_citilink(query: str, limit: int = 36) -> list[dict]:
    page = _get_citi_page()
    url = f"https://www.citilink.ru/search/?text={quote(query)}"
    logger.info("citilink search: %r -> %s", query, url)
    page.goto(url, wait_until="load", timeout=45000)
    logger.info("citilink search: page loaded for %r", query)
    try:
        page.wait_for_selector("[data-meta-product-id]", timeout=10000)
    except Exception:
        pass

    cards = page.evaluate("""
        () => {
            var cards = document.querySelectorAll('[data-meta-product-id]');
            var result = [];
            for (var i = 0; i < cards.length; i++) {
                var c = cards[i];
                var a = c.querySelector('a[href*="/product/"]');
                if (!a) continue;
                var name = a.getAttribute('title') || '';
                if (!name) {
                    var links = c.querySelectorAll('a[href*="/product/"]');
                    for (var j = 0; j < links.length; j++) {
                        var t = links[j].innerText.trim().split('\\n')[0];
                        if (t.length > 5) { name = t; break; }
                    }
                }
                var img = c.querySelector('img[src]');
                var imgSrc = '';
                if (img) {
                    imgSrc = img.getAttribute('src') || img.getAttribute('data-src') || '';
                    if (imgSrc.startsWith('//')) imgSrc = 'https:' + imgSrc;
                }
                result.push({
                    id: c.getAttribute('data-meta-product-id'),
                    href: a.href,
                    name: name,
                    image_url: imgSrc
                });
            }
            return result;
        }
    """)
    seen = set()
    unique = []
    for c in (cards or []):
        pid = c.get("id")
        if pid and pid not in seen and c.get("href"):
            seen.add(pid)
            unique.append(c)
    logger.info("citilink search: found %d products for %r", len(unique[:limit]), query)
    return unique[:limit]


# ── Характеристики товара ─────────────────────────────────────────────────────

def _get_properties(product_url: str) -> tuple[dict, float | None]:
    page = _get_citi_page()
    props_url = product_url.rstrip("/") + "/properties/"
    logger.info("citilink props: %s", props_url)
    page.goto(props_url, wait_until="load", timeout=45000)
    logger.info("citilink props: loaded")
    try:
        # Wait for the detailed spec groups (only appear after full load)
        page.wait_for_selector('[class*="PropertyGroupWrapper"]', timeout=12000)
    except Exception:
        try:
            page.wait_for_selector('[class*="PropertiesItem"]', timeout=5000)
        except Exception:
            pass

    data = page.evaluate("""
        () => {
            var result = {};
            // Detailed table: PropertyGroupWrapper -> PropertiesItem
            var items = document.querySelectorAll('[class*="PropertyGroupWrapper"] [class*="PropertiesItem"]');
            if (items.length === 0) {
                items = document.querySelectorAll('[class*="PropertiesItem"]');
            }
            items.forEach(function(el) {
                var nameEl = el.querySelector('[class*="PropertiesName"]');
                var valEl  = el.querySelector('[class*="PropertiesValue"]');
                if (nameEl && valEl) {
                    var name = nameEl.innerText.trim().replace(/:$/, '');
                    var val  = valEl.innerText.trim();
                    if (name && val && name.length < 80) result[name] = val;
                }
            });
            return result;
        }
    """)

    price_raw = page.evaluate("""
        () => {
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
            var all = document.querySelectorAll('*');
            for (var i = 0; i < all.length; i++) {
                var t = all[i].childNodes;
                for (var j = 0; j < t.length; j++) {
                    if (t[j].nodeType === 3 && t[j].textContent.includes('\\u20bd')) {
                        var txt = t[j].textContent.trim();
                        if (/^\\d[\\d\\s]*\\u20bd/.test(txt)) return txt;
                    }
                }
            }
            return null;
        }
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
    sensor_raw = _get(props, "Сенсор")
    sensor = None if (sensor_raw and re.search(r'\d.*dpi', sensor_raw, re.IGNORECASE)) else sensor_raw
    return {
        "brand":            _get(props, "Бренд"),
        "connection_types": _get(props, "Тип соединения мыши", "Тип подключения мыши"),
        "interface":        _get(props, "Интерфейс подключения", "Интерфейс"),
        "sensor":           sensor,
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
        "keyboard_type":        _get(props, "Тип клавиатуры"),
        "switches":             _get(props, "Тип переключателей", "Переключатели"),
        "form_factor":          _get(props, "Форм-фактор", "Конструкция"),
        "board_material":       _get(props, "Материал корпуса"),
        "keycap_material":      _get(props, "Материал клавиш", "Материал кейкапов"),
        "keycap_manufacturing": _get(props, "Способ нанесения символов", "Нанесение символов"),
        "connection_types":     _get(props, "Тип подключения"),
        "interface":            _get(props, "Интерфейс", "Интерфейс подключения"),
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
        "connection_types":  _get(props, "Тип подключения"),
        "interface":         _get(props, "Интерфейс подключения", "Интерфейс"),
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
        "connection_types": _get(props, "Тип подключения"),
        "interface":        _get(props, "Интерфейс подключения", "Интерфейс"),
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

# Слова, которые не являются брендом или моделью
_STOP_WORDS = {
    "мышь", "мыши", "клавиатура", "клавиатуры", "монитор", "наушники", "микрофон",
    "коврик", "гарнитура", "проводная", "беспроводная", "игровая", "игровой",
    "оптическая", "оптический", "механическая", "конденсаторный", "usb", "usb-c",
    "rgb", "led", "wireless", "wired", "gaming", "pro", "для", "и", "с", "без",
    "черный", "белый", "серый", "красный", "синий", "черная", "белая", "серебристый",
}


def _extract_model_tokens(name: str) -> set[str]:
    """
    Extract brand + model identifiers from product name.
    Captures: brand names (start with uppercase) + model codes (contain digits).
    Returns lowercase tokens.
    """
    name_clean = re.sub(r"[,/|;()%]", " ", name)
    tokens = name_clean.split()
    result = set()
    for tok in tokens:
        raw = tok.strip()
        t = raw.lower()
        if len(t) < 2 or t in _STOP_WORDS:
            continue
        # Brand: starts with uppercase original form and not a Russian word
        if raw[0].isupper() and not re.search(r"[а-яё]", raw, re.IGNORECASE):
            result.add(t)
        # Model code: contains at least one digit
        elif re.search(r"\d", t):
            result.add(t)
    return result


def _name_similarity(a: str, b: str) -> float:
    a = re.sub(r"\s+", " ", a.lower().strip())
    b = re.sub(r"\s+", " ", b.lower().strip())
    return SequenceMatcher(None, a, b).ratio()


def _find_by_name(db, model_class, name: str, threshold: float = 0.82):
    """
    Match Citilink product to an existing DB record.

    Strategy (in order of confidence):
    1. Token overlap: brand + model codes must share ≥2 tokens — exact model identity.
    2. Fuzzy fallback at high threshold (0.82) for names without clear model codes.
    Only one candidate may survive; if multiple pass step 1, use fuzzy to pick best.
    """
    candidates = db.query(model_class).filter(
        model_class.citilink_sku == None,
        model_class.name != None,
    ).all()
    if not candidates:
        return None

    citi_tokens = _extract_model_tokens(name)

    # Step 1: token-overlap matching (high confidence)
    citi_model_codes = {t for t in citi_tokens if re.search(r"\d", t)}

    scored = []
    for row in candidates:
        row_tokens = _extract_model_tokens(row.name or "")
        shared = citi_tokens & row_tokens
        if not shared:
            continue

        row_model_codes = {t for t in row_tokens if re.search(r"\d", t)}

        # Conflicting model codes: one side has digit-codes the other doesn't share
        # e.g. "G502 Hero" vs "G502 X": both have g502 but "hero" ≠ nothing/X
        citi_only_codes = citi_model_codes - row_model_codes
        row_only_codes  = row_model_codes  - citi_model_codes
        has_conflict = bool(citi_only_codes) or bool(row_only_codes)

        # Model code shared — counts double
        model_overlap = citi_model_codes & row_model_codes
        score = len(shared) + len(model_overlap)

        # If there are conflicting model codes, disqualify immediately
        if has_conflict:
            continue

        scored.append((score, row))

    if scored:
        scored.sort(key=lambda x: (
            -x[0],
            -_name_similarity(name, x[1].name or ""),
        ))
        best_score_val, best_row = scored[0]

        has_model_code_match = bool(
            citi_model_codes & _extract_model_tokens(best_row.name or "")
        )
        min_score = 2 if has_model_code_match else 3

        if best_score_val < min_score:
            pass  # fall through to fuzzy
        elif len(scored) == 1 or scored[0][0] > scored[1][0]:
            return best_row
        else:
            if _name_similarity(name, best_row.name or "") >= threshold:
                return best_row
            return None

    # Step 2: fuzzy fallback (lower confidence, higher threshold)
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
    exclude_name_kw: list[str] | None = None,
) -> dict:
    added = updated = failed = skipped = 0
    seen_ids: set[str] = set()

    for query in queries:
        try:
            products = _search_citilink(query, limit=36)
        except Exception as e:
            logger.error("citilink search failed for query=%r: %s", query, e, exc_info=True)
            if "ERR_NAME_NOT_RESOLVED" in str(e) or "ERR_CONNECTION_RESET" in str(e):
                _reset_citi_page()
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

                base_url = re.sub(r"/properties/?$", "", href).rstrip("/") + "/"
                citilink_url = base_url

                props, citilink_price = _get_properties(base_url)
                if not props:
                    skipped += 1
                    continue

                chars = char_mapper(props)
                name = product.get("name") or ""
                if not name:
                    name = _get_citi_page().evaluate(
                        "() => { var h = document.querySelector('h1'); return h ? h.innerText : ''; }"
                    ) or citilink_sku
                if exclude_name_kw and any(kw.lower() in name.lower() for kw in exclude_name_kw):
                    skipped += 1
                    continue
                brand = chars.pop("brand", None)
                if not brand and name:
                    first = name.strip().split()[0]
                    if (len(first) > 1
                            and not re.match(r"^\d+(\.\d+)?$", first)
                            and not re.search(r"(ный|ной|вой|ской|ский|ная|ное)$", first, re.IGNORECASE)):
                        brand = first

                if required_fields and all(chars.get(f) is None for f in required_fields):
                    skipped += 1
                    continue

                existing = db.query(model_class).filter(
                    model_class.citilink_sku == citilink_sku
                ).first()
                if existing:
                    if citilink_price is not None:
                        existing.citilink_price = citilink_price
                    for f, v in chars.items():
                        if v is not None and getattr(existing, f, None) is None:
                            setattr(existing, f, v)
                    db.commit()
                    updated += 1
                    continue

                image_url = product.get("image_url") or None

                matched = _find_by_name(db, model_class, name)
                if matched:
                    matched.citilink_sku = citilink_sku
                    matched.citilink_url = citilink_url
                    matched.citilink_price = citilink_price
                    if image_url and not matched.image_url:
                        matched.image_url = image_url
                    for f, v in chars.items():
                        if v is not None and getattr(matched, f, None) is None:
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
                        image_url=image_url,
                        **chars,
                    ))
                    db.commit()
                    added += 1

                time.sleep(random.uniform(2.0, 4.0))

            except Exception as e:
                logger.error("citilink product processing error: %s", e, exc_info=True)
                failed += 1
                db.rollback()
                if "ERR_NAME_NOT_RESOLVED" in str(e) or "ERR_CONNECTION_RESET" in str(e):
                    _reset_citi_page()

        time.sleep(random.uniform(8.0, 15.0))

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
    ], Microphone, _map_microphone, required_fields=["mic_type"],
    exclude_name_kw=["съёмный", "сменный", "для гарнитур", "для наушник"])


def parse_mousepads(db: Session) -> dict:
    return _run_parse(db, [
        "игровой коврик для мыши xl", "коврик rgb игровой",
        "коврик logitech steelseries",
    ], Mousepad, _map_mousepad, required_fields=["surface_material"])
