import re
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from app.models.mouse import Mouse
from app.models.keyboard import Keyboard
from app.models.monitor import Monitor
from app.models.headphones import Headphones
from app.models.microphone import Microphone
from app.models.mousepad import Mousepad

_MODEL_MAP = {
    "mouse": Mouse,
    "keyboard": Keyboard,
    "monitor": Monitor,
    "headphones": Headphones,
    "microphone": Microphone,
    "mousepad": Mousepad,
}

_SWITCH_KEYWORDS: dict[str, list[str]] = {
    "linear": ["Red", "Silver", "Speed", "Yellow", "Black", "линейн", "linear", "Cream", "Amber", "Mute"],
    "tactile": ["Brown", "Clear", "Tactile", "тактильн", "White"],
    "clicky": ["Blue", "Green", "Clicky", "кликающ", "Зелен", "Purple"],
    "magnetic": ["Magnetic", "Hall", "магнитн", "halleffect"],
}

# Brand quality tiers per category.
# Tier 3 = топовые игровые бренды, 2 = хорошие, 1 = бюджетные игровые,
# 0 = нейтральные, -1 = дешёвые ноунейм
_BRAND_TIER: dict[str, dict[str, int]] = {
    "mouse": {
        "logitech": 3, "razer": 3, "steelseries": 3, "zowie": 3,
        "glorious": 3, "pulsar": 3, "vaxee": 3, "endgame gear": 3, "xlr8": 2,
        "hyperx": 2, "corsair": 2, "asus": 2, "msi": 2, "roccat": 2, "cooler master": 2,
        "nzxt": 2, "xtrfy": 2, "alienware": 2,
        "bloody": 1, "a4tech": 1, "redragon": 1, "dareu": 1, "fantech": 1,
        "ajazz": 1, "attack shark": 1, "acer": 1, "lenovo": 1, "viper": 1,
        "defender": 0, "trust": 0, "microsoft": 0, "oklick": 0,
        "gembird": -1, "herler": -1, "smartbuy": -1, "sven": -1,
    },
    "keyboard": {
        "logitech": 3, "razer": 3, "steelseries": 3, "keychron": 3,
        "ducky": 3, "leopold": 3, "varmilo": 3, "hhkb": 3, "realforce": 3,
        "hyperx": 2, "corsair": 2, "asus": 2, "cooler master": 2, "roccat": 2,
        "glorious": 2, "epomaker": 2, "nzxt": 2, "msi": 2,
        "bloody": 1, "a4tech": 1, "redragon": 1, "dareu": 1,
        "royal kludge": 1, "ajazz": 1, "aula": 1, "tecware": 1, "akko": 1,
        "defender": 0, "oklick": 0, "microsoft": 0,
        "gembird": -1, "smartbuy": -1,
    },
    "monitor": {
        "lg": 3, "samsung": 3, "asus": 3, "dell": 3, "benq": 3, "viewsonic": 3,
        "msi": 2, "gigabyte": 2, "philips": 2, "iiyama": 2, "aoc": 2, "eizo": 3,
        "acer": 2, "hp": 1, "lenovo": 1,
    },
    "headphones": {
        "logitech": 3, "razer": 3, "steelseries": 3, "hyperx": 3,
        "sennheiser": 3, "beyerdynamic": 3, "sony": 3, "bose": 3, "audio-technica": 3,
        "corsair": 2, "asus": 2, "roccat": 2, "jbl": 2, "jabra": 2, "skullcandy": 2,
        "redragon": 1, "bloody": 1, "dareu": 1, "sven": 1, "a4tech": 1,
        "defender": 0, "oklick": 0,
        "gembird": -1, "smartbuy": -1,
    },
    "microphone": {
        "blue": 3, "rode": 3, "sennheiser": 3, "shure": 3, "elgato": 3, "audio-technica": 3,
        "hyperx": 3, "razer": 2, "logitech": 2, "maono": 2, "fifine": 2, "samson": 2,
        "trust gaming": 1, "a4tech": 1,
        "defender": 0, "gembird": -1,
    },
    "mousepad": {
        "steelseries": 3, "logitech": 3, "razer": 3, "glorious": 3, "endgame gear": 3,
        "artisan": 3, "corsair": 2, "hyperx": 2, "asus": 2, "msi": 2, "roccat": 2,
        "redragon": 1, "bloody": 1, "a4tech": 1,
        "defender": 0, "gembird": -1,
    },
}

# Minimum price ratio relative to budget per priority mode
_MIN_PRICE_RATIO = {"budget": 0.05, "balance": 0.15, "flagship": 0.40}


def _best_price(product) -> float | None:
    prices = [p for p in [product.price, product.wb_price, product.citilink_price] if p is not None]
    return min(prices) if prices else None


def _brand_score(product, category: str) -> int:
    brand = (product.brand or "").lower().strip()
    if not brand:
        return 0
    tier_map = _BRAND_TIER.get(category, {})
    if brand in tier_map:
        return tier_map[brand]
    for key, val in tier_map.items():
        if key in brand:  # e.g. "logitech" in "logitech g pro series"
            return val
    return 0


def _parse_max_dim(size_str: str) -> int | None:
    nums = re.findall(r'\d+', size_str or "")
    if not nums:
        return None
    return max(int(n) for n in nums[:2])


def _filter_mousepad_size(products: list, size_pref: str | None) -> list:
    if not size_pref or size_pref == "any":
        return products
    result = []
    for p in products:
        dim = _parse_max_dim(p.size or "")
        if dim is None:
            result.append(p)
            continue
        if size_pref == "small" and dim < 350:
            result.append(p)
        elif size_pref == "large" and dim >= 350:
            result.append(p)
    return result


def recommend(category: str, answers: dict, db: Session) -> list[dict]:
    model = _MODEL_MAP[category]
    products = _build_query(category, answers, db, model).all()

    if category == "mousepad":
        products = _filter_mousepad_size(products, answers.get("size"))

    scored = [
        (p, *_score(p, category, answers))
        for p in products
    ]
    priority = answers.get("priority", "balance")
    if priority == "flagship":
        # Flagship: при равных баллах — дороже лучше
        scored.sort(key=lambda x: (-x[1], -(_best_price(x[0]) or 0)))
    elif priority == "budget":
        # Budget: при равных баллах — дешевле лучше
        scored.sort(key=lambda x: (-x[1], _best_price(x[0]) or float("inf")))
    else:
        # Balance: при равных баллах — ближе к середине бюджета лучше
        budget_f = float(answers.get("budget") or 0)
        def balance_key(x):
            price = _best_price(x[0]) or 0
            mid = budget_f * 0.6
            return (-x[1], abs(price - mid))
        scored.sort(key=balance_key)

    def _attr(p, field: str):
        return getattr(p, field, None)

    return [
        {
            "id": p.id,
            "name": p.name,
            "brand": p.brand,
            "price": p.price,
            "wb_price": p.wb_price,
            "citilink_price": p.citilink_price,
            "best_price": _best_price(p),
            "score": score,
            "score_breakdown": breakdown,
            "image_url": p.image_url,
            "ozon_url": p.ozon_url,
            "dns_url": p.dns_url,
            "wb_url": p.wb_url,
            "citilink_url": p.citilink_url,
            "updated_at": p.updated_at,
            # Characteristics (field may not exist on all models — safe via getattr)
            "sensor":             _attr(p, "sensor"),
            "weight_g":           _attr(p, "weight_g"),
            "max_dpi":            _attr(p, "max_dpi"),
            "button_count":       _attr(p, "button_count"),
            "connection_types":   _attr(p, "connection_types"),
            "has_rgb":            _attr(p, "has_rgb"),
            "color":              _attr(p, "color"),
            "keyboard_type":      _attr(p, "keyboard_type"),
            "switches":           _attr(p, "switches"),
            "form_factor":        _attr(p, "form_factor"),
            "key_count":          _attr(p, "key_count"),
            "layout":             _attr(p, "layout"),
            "keycap_material":    _attr(p, "keycap_material"),
            "keycap_manufacturing": _attr(p, "keycap_manufacturing"),
            "diagonal_inch":      _attr(p, "diagonal_inch"),
            "resolution":         _attr(p, "resolution"),
            "refresh_rate_hz":    _attr(p, "refresh_rate_hz"),
            "matrix_type":        _attr(p, "matrix_type"),
            "response_time_ms":   _attr(p, "response_time_ms"),
            "construction_type":  _attr(p, "construction_type"),
            "has_microphone":     _attr(p, "has_microphone"),
            "impedance_ohm":      _attr(p, "impedance_ohm"),
            "frequency_response": _attr(p, "frequency_response"),
            "mic_type":           _attr(p, "mic_type"),
            "directionality":     _attr(p, "directionality"),
            "frequency_range":    _attr(p, "frequency_range"),
            "size":               _attr(p, "size"),
            "surface_material":   _attr(p, "surface_material"),
            "thickness_mm":       _attr(p, "thickness_mm"),
        }
        for p, score, breakdown in scored[:20]
    ]


def _build_query(category: str, answers: dict, db: Session, model):
    query = db.query(model)

    # Only products with at least one known price (in stock somewhere)
    query = query.filter(
        or_(
            model.price.isnot(None),
            model.wb_price.isnot(None),
            model.citilink_price.isnot(None),
        )
    )

    budget = answers.get("budget")
    priority = answers.get("priority", "balance")

    if budget is not None:
        budget_f = float(budget)

        # Upper limit: at least one source must be within budget
        query = query.filter(
            or_(
                model.price <= budget_f,
                model.wb_price <= budget_f,
                model.citilink_price <= budget_f,
            )
        )

        # Lower limit: best_price (min across sources) must be >= min_price.
        # Use AND: every non-null price must clear the threshold, so a cheap
        # citilink_price=200 with an expensive wb_price=18000 doesn't sneak through.
        min_price = budget_f * _MIN_PRICE_RATIO.get(priority, 0.15)
        if min_price >= 100:
            query = query.filter(
                and_(
                    or_(model.price == None, model.price >= min_price),
                    or_(model.wb_price == None, model.wb_price >= min_price),
                    or_(model.citilink_price == None, model.citilink_price >= min_price),
                )
            )

    if category == "mouse":
        wireless = answers.get("wireless")
        if wireless == "yes":
            query = query.filter(
                model.connection_types.ilike("%беспровод%") |
                model.connection_types.ilike("%bluetooth%")
            )
        elif wireless == "no":
            query = query.filter(
                model.connection_types.ilike("%провод%"),
                ~model.connection_types.ilike("%беспровод%"),
            )

    elif category == "keyboard":
        form_factor = answers.get("form_factor")
        if form_factor == "full":
            query = query.filter(
                model.form_factor.ilike("%полноразмерная%") |
                model.form_factor.ilike("%full%")
            )
        elif form_factor == "tkl":
            query = query.filter(
                model.form_factor.ilike("%tkl%") |
                model.form_factor.ilike("%80%") |
                model.form_factor.ilike("%без цифровой%")
            )
        elif form_factor == "compact":
            query = query.filter(
                model.form_factor.ilike("%компактная%") |
                model.form_factor.ilike("%60%") |
                model.form_factor.ilike("%65%") |
                model.form_factor.ilike("%75%") |
                model.form_factor.ilike("%96%")
            ).filter(
                ~model.form_factor.ilike("%tkl%"),
                ~model.form_factor.ilike("%80%"),
            )

    elif category == "monitor":
        size = answers.get("size")
        if size == "small":
            query = query.filter(model.diagonal_inch < 24)
        elif size == "medium":
            query = query.filter(model.diagonal_inch >= 24, model.diagonal_inch < 27)
        elif size == "large":
            query = query.filter(model.diagonal_inch >= 27)

    elif category == "headphones":
        construction = answers.get("construction_type")
        if construction == "fullsize":
            query = query.filter(
                model.construction_type.ilike("%полноразмер%") |
                model.construction_type.ilike("%накладн%")
            )
        elif construction == "earbuds":
            query = query.filter(
                model.construction_type.ilike("%вкладыш%") |
                model.construction_type.ilike("%внутриканальн%")
            )
        connection = answers.get("connection")
        if connection == "wired":
            query = query.filter(
                model.connection_types.ilike("%провод%"),
                ~model.connection_types.ilike("%беспровод%"),
            )
        elif connection == "wireless":
            query = query.filter(
                model.connection_types.ilike("%беспровод%") |
                model.connection_types.ilike("%bluetooth%") |
                model.connection_types.ilike("%tws%")
            )

    elif category == "microphone":
        connection = answers.get("connection")
        if connection == "usb":
            query = query.filter(
                model.interface.ilike("%usb%") |
                model.connection_types.ilike("%usb%")
            )
        elif connection == "xlr":
            query = query.filter(
                model.interface.ilike("%xlr%") |
                model.connection_types.ilike("%xlr%")
            )

    elif category == "mousepad":
        hardness = answers.get("hardness")
        if hardness == "soft":
            query = query.filter(
                model.surface_material.ilike("%ткань%") |
                model.surface_material.ilike("%текстиль%") |
                model.surface_material.ilike("%нейлон%") |
                model.surface_material.ilike("%полиэстер%") |
                model.surface_material.ilike("%микрофибра%") |
                model.surface_material.ilike("%велюр%") |
                model.hardness.ilike("%мягк%")
            )
        elif hardness == "hard":
            query = query.filter(
                model.surface_material.ilike("%пластик%") |
                model.surface_material.ilike("%eva%") |
                model.surface_material.ilike("%стекл%") |
                model.surface_material.ilike("%акрил%") |
                model.hardness.ilike("%жёстк%") |
                model.hardness.ilike("%жестк%")
            )
        rgb = answers.get("rgb")
        if rgb == "yes":
            query = query.filter(model.has_rgb == True)
        elif rgb == "no":
            # isnot(True) включает и False, и NULL — без RGB значит без RGB
            query = query.filter(model.has_rgb.isnot(True))

    return query


def _score(product, category: str, answers: dict) -> tuple[int, list[dict]]:
    """Returns (total_score, breakdown_list)."""
    score = 0
    breakdown: list[dict] = []
    budget = answers.get("budget")
    priority = answers.get("priority", "balance")
    use_case = answers.get("use_case")
    best = _best_price(product)

    def add(pts: int, label: str) -> None:
        nonlocal score
        if pts == 0:
            return
        score += pts
        breakdown.append({"label": label, "points": pts, "positive": pts > 0})

    # ── 1. Репутация бренда ────────────────────────────────────────────────────
    brand_pts = _brand_score(product, category)
    brand_multiplier = {"budget": 0, "balance": 1, "flagship": 2}
    final_brand = brand_pts * brand_multiplier.get(priority, 1)
    if final_brand != 0:
        brand_name = (product.brand or "").strip() or "бренд"
        tier_labels = {3: "топ-уровень", 2: "хороший бренд", 1: "бюджетный игровой", -1: "ноунейм"}
        tier_label = tier_labels.get(brand_pts, "")
        add(final_brand, f"Бренд {brand_name}{' — ' + tier_label if tier_label else ''}")

    # ── 2. Использование бюджета ───────────────────────────────────────────────
    if budget is not None and best is not None:
        ratio = best / float(budget)
        pct = int(ratio * 100)
        if priority == "flagship":
            if ratio >= 0.75:
                add(6, f"Цена {pct}% бюджета — максимум для флагмана")
            elif ratio >= 0.55:
                add(4, f"Цена {pct}% бюджета — оптимально для флагмана")
            elif ratio >= 0.40:
                add(1, f"Цена {pct}% бюджета — в рамках флагмана")
            elif ratio < 0.40:
                add(-4, f"Цена {pct}% бюджета — слишком дёшево для флагмана")
        elif priority == "budget":
            if 0.15 <= ratio <= 0.50:
                add(3, f"Цена {pct}% бюджета — хорошая экономия")
            elif ratio <= 0.70:
                add(1, f"Цена {pct}% бюджета")
        else:
            if 0.30 <= ratio <= 0.85:
                add(3, f"Цена {pct}% бюджета — оптимальный диапазон")
            elif ratio < 0.15:
                add(-3, f"Цена {pct}% бюджета — слишком дёшево")

    # ── 3. Качество характеристик ──────────────────────────────────────────────

    if category == "mouse":
        if use_case == "gaming":
            if product.weight_g is not None:
                if product.weight_g <= 60:
                    add(4, f"Вес {product.weight_g} г — ультралёгкая")
                elif product.weight_g <= 80:
                    add(3, f"Вес {product.weight_g} г — лёгкая для гейминга")
                elif product.weight_g <= 100:
                    add(1, f"Вес {product.weight_g} г — приемлемый")
            if product.max_dpi is not None:
                if product.max_dpi >= 25000:
                    add(3, f"Сенсор {product.max_dpi} DPI — премиум")
                elif product.max_dpi >= 12000:
                    add(2, f"Сенсор {product.max_dpi} DPI — высокий")
                elif product.max_dpi >= 6000:
                    add(1, f"Сенсор {product.max_dpi} DPI")
        elif use_case == "office":
            if product.weight_g is not None and 80 <= product.weight_g <= 130:
                add(1, f"Вес {product.weight_g} г — удобно для работы")

    elif category == "keyboard":
        switches_pref = answers.get("switches")
        if switches_pref and switches_pref != "any" and product.switches:
            keywords = _SWITCH_KEYWORDS.get(switches_pref, [])
            if any(kw.lower() in product.switches.lower() for kw in keywords):
                add(3, f"Переключатели {product.switches} — соответствуют выбору")
        if use_case == "gaming" and product.form_factor and any(
            kw in product.form_factor.lower() for kw in ("tkl", "полноразмерная", "full")
        ):
            add(1, f"Форм-фактор {product.form_factor} — подходит для игр")
        if product.key_count is not None and product.key_count >= 100 and use_case != "gaming":
            add(1, f"{product.key_count} клавиш — полный набор")

    elif category == "monitor":
        if use_case == "gaming":
            if product.refresh_rate_hz is not None:
                if product.refresh_rate_hz >= 360:
                    add(6, f"{product.refresh_rate_hz} Гц — топ для гейминга")
                elif product.refresh_rate_hz >= 240:
                    add(5, f"{product.refresh_rate_hz} Гц — отлично для игр")
                elif product.refresh_rate_hz >= 165:
                    add(4, f"{product.refresh_rate_hz} Гц — хорошо для игр")
                elif product.refresh_rate_hz >= 144:
                    add(3, f"{product.refresh_rate_hz} Гц — подходит для гейминга")
        elif use_case == "work":
            if product.matrix_type and "ips" in product.matrix_type.lower():
                add(3, f"Матрица {product.matrix_type} — отличная цветопередача")
            if product.resolution and "3840" in product.resolution:
                add(2, "Разрешение 4K — высокая детализация")
            if product.refresh_rate_hz is not None and product.refresh_rate_hz >= 144:
                add(-2, f"{product.refresh_rate_hz} Гц — лишнее для работы")
            if product.name and "игров" in product.name.lower():
                add(-2, "Игровая модель — не оптимальна для работы")
        elif use_case == "both":
            if product.matrix_type and "ips" in product.matrix_type.lower():
                add(2, f"Матрица {product.matrix_type} — хорошая цветопередача")
            if product.refresh_rate_hz is not None and product.refresh_rate_hz >= 144:
                add(2, f"{product.refresh_rate_hz} Гц — универсальный выбор")

    elif category == "headphones":
        if use_case == "gaming" and product.has_microphone:
            add(2, "Встроенный микрофон — нужен для игр")
        if use_case == "music" and not product.has_microphone:
            add(1, "Без микрофона — чистый звук для музыки")
        if use_case == "calls" and product.has_microphone:
            add(3, "Встроенный микрофон — необходим для звонков")

    elif category == "microphone":
        if use_case == "streaming" and product.mic_type and "конденсаторный" in product.mic_type.lower():
            add(2, "Конденсаторный микрофон — идеален для стриминга")
        if use_case == "calls":
            iface = (product.interface or "") + " " + (product.connection_types or "")
            if "usb" in iface.lower():
                add(2, "USB подключение — plug & play для звонков")

    elif category == "mousepad":
        rgb_pref = answers.get("rgb")
        if rgb_pref == "yes" and product.has_rgb:
            add(2, "RGB-подсветка — соответствует выбору")
        elif rgb_pref == "no" and not product.has_rgb:
            add(1, "Без RGB — соответствует выбору")

    return score, breakdown
