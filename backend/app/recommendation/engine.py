import re
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from app.recommendation import scoring
from app.recommendation.scoring import best_price as _best_price, representative_rating
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

# Minimum price ratio relative to budget per priority mode
_MIN_PRICE_RATIO = {"budget": 0.05, "balance": 0.15, "flagship": 0.40}


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


def _compute_brand_avgs(db: Session, model) -> dict[str, tuple[float, int]]:
    """Per-brand review-weighted average rating over the whole category."""
    acc: dict[str, list[float]] = {}  # brand_lower -> [sum_weighted, sum_reviews]
    for p in db.query(model).all():
        r, v = representative_rating(p)
        if r is None or not v:
            continue
        b = (p.brand or "").lower().strip()
        if not b:
            continue
        a = acc.setdefault(b, [0.0, 0.0])
        a[0] += r * v
        a[1] += v
    return {b: (s / v, int(v)) for b, (s, v) in acc.items() if v > 0}


def recommend(category: str, answers: dict, db: Session) -> list[dict]:
    model = _MODEL_MAP[category]
    products = _build_query(category, answers, db, model).all()

    if category == "mousepad":
        products = _filter_mousepad_size(products, answers.get("size"))

    brand_avgs = _compute_brand_avgs(db, model)
    scored = [
        (p, *scoring.score_product(p, category, answers, brand_avgs))
        for p in products
    ]
    priority = answers.get("priority", "balance")
    if priority == "flagship":
        scored.sort(key=lambda x: (-x[1], -(_best_price(x[0]) or 0)))
    elif priority == "budget":
        scored.sort(key=lambda x: (-x[1], _best_price(x[0]) or float("inf")))
    else:
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
            "ozon_rating":      _attr(p, "ozon_rating"),
            "ozon_reviews":     _attr(p, "ozon_reviews"),
            "citilink_rating":  _attr(p, "citilink_rating"),
            "citilink_reviews": _attr(p, "citilink_reviews"),
            "wb_rating":        _attr(p, "wb_rating"),
            "wb_reviews":       _attr(p, "wb_reviews"),
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


