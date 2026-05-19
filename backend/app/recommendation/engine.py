from sqlalchemy import or_
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

# Ключевые слова в названии переключателей для каждого типа
_SWITCH_KEYWORDS: dict[str, list[str]] = {
    "linear": ["Red", "Silver", "Speed", "Yellow", "Black"],
    "tactile": ["Brown", "Clear", "Tactile"],
    "clicky": ["Blue", "Green", "Clicky"],
}


def _best_price(product) -> float | None:
    prices = [p for p in [product.price, product.wb_price, product.citilink_price] if p is not None]
    return min(prices) if prices else None


def recommend(category: str, answers: dict, db: Session) -> list[dict]:
    model = _MODEL_MAP[category]
    products = _build_query(category, answers, db, model).all()

    scored = [(p, _score(p, category, answers)) for p in products]
    scored.sort(key=lambda x: (-x[1], _best_price(x[0]) or 0))

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
            "image_url": p.image_url,
            "ozon_url": p.ozon_url,
            "dns_url": p.dns_url,
            "wb_url": p.wb_url,
            "citilink_url": p.citilink_url,
        }
        for p, score in scored[:20]
    ]


def _build_query(category: str, answers: dict, db: Session, model):
    query = db.query(model)

    budget = answers.get("budget")
    if budget is not None:
        budget = float(budget)
        query = query.filter(
            or_(
                model.price <= budget,
                model.wb_price <= budget,
                model.citilink_price <= budget,
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
            query = query.filter(model.form_factor == "Full")
        elif form_factor == "tkl":
            query = query.filter(model.form_factor == "TKL")
        elif form_factor == "compact":
            query = query.filter(model.form_factor.in_(["60%", "65%", "75%"]))

    elif category == "monitor":
        size = answers.get("size")
        if size == "small":
            query = query.filter(model.diagonal_inch <= 24)
        elif size == "medium":
            query = query.filter(model.diagonal_inch >= 24, model.diagonal_inch <= 27)
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
            query = query.filter(model.connection_types.ilike("%usb%"))
        elif connection == "xlr":
            query = query.filter(model.connection_types.ilike("%xlr%"))

    elif category == "mousepad":
        hardness = answers.get("hardness")
        if hardness == "soft":
            query = query.filter(
                model.surface_material.ilike("%ткань%") |
                model.surface_material.ilike("%текстиль%") |
                model.surface_material.ilike("%нейлон%") |
                model.surface_material.ilike("%полиэстер%")
            )
        elif hardness == "hard":
            query = query.filter(
                model.surface_material.ilike("%пластик%") |
                model.surface_material.ilike("%eva%")
            )

        rgb = answers.get("rgb")
        if rgb == "yes":
            query = query.filter(model.has_rgb == True)
        elif rgb == "no":
            query = query.filter(model.has_rgb == False)

    return query


def _score(product, category: str, answers: dict) -> int:
    score = 0
    budget = answers.get("budget")

    # +2 если товар стоит не больше 70% от бюджета — выгодная покупка
    if budget is not None and product.price is not None:
        if product.price <= float(budget) * 0.7:
            score += 2

    use_case = answers.get("use_case")

    if category == "mouse":
        if use_case == "gaming" and product.weight_g is not None and product.weight_g <= 80:
            score += 3  # лёгкая мышь — стандарт для игр
        elif use_case == "office" and product.weight_g is not None and product.weight_g >= 90:
            score += 1

    elif category == "keyboard":
        switches_pref = answers.get("switches")
        if switches_pref and switches_pref != "any" and product.switches:
            keywords = _SWITCH_KEYWORDS.get(switches_pref, [])
            if any(kw.lower() in product.switches.lower() for kw in keywords):
                score += 3  # переключатели совпали с предпочтением
        if use_case == "gaming" and product.form_factor in ("TKL", "Full"):
            score += 1

    elif category == "monitor":
        if use_case == "gaming":
            if product.refresh_rate_hz is not None and product.refresh_rate_hz >= 144:
                score += 3
        elif use_case == "work":
            if product.matrix_type and product.matrix_type.upper() == "IPS":
                score += 3
            if product.refresh_rate_hz is not None and product.refresh_rate_hz >= 144:
                score -= 3  # высокий Hz — признак игрового монитора
            if product.name and "игров" in product.name.lower():
                score -= 2  # явно игровой — не подходит для работы

    elif category == "headphones":
        if use_case == "gaming" and product.has_microphone:
            score += 2  # гарнитура с микрофоном удобна для игр
        if use_case == "music" and not product.has_microphone:
            score += 1  # без микрофона — чище звук для музыки
        if use_case == "calls" and product.has_microphone:
            score += 3  # микрофон обязателен для звонков

    elif category == "microphone":
        if use_case == "streaming" and product.mic_type and "конденсаторный" in product.mic_type.lower():
            score += 2  # конденсаторный лучше для стриминга
        if use_case == "calls" and product.connection_types and "usb" in product.connection_types.lower():
            score += 2  # USB удобен для звонков без дополнительного оборудования

    elif category == "mousepad":
        if product.has_rgb:
            score += 1  # подсветка — приятный бонус

    return score
