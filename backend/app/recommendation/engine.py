from sqlalchemy.orm import Session
from app.models.mouse import Mouse
from app.models.keyboard import Keyboard
from app.models.monitor import Monitor

_MODEL_MAP = {
    "mouse": Mouse,
    "keyboard": Keyboard,
    "monitor": Monitor,
}

# Ключевые слова в названии переключателей для каждого типа
_SWITCH_KEYWORDS: dict[str, list[str]] = {
    "linear": ["Red", "Silver", "Speed", "Yellow", "Black"],
    "tactile": ["Brown", "Clear", "Tactile"],
    "clicky": ["Blue", "Green", "Clicky"],
}


def recommend(category: str, answers: dict, db: Session) -> list[dict]:
    model = _MODEL_MAP[category]
    products = _build_query(category, answers, db, model).all()

    scored = [(p, _score(p, category, answers)) for p in products]
    scored.sort(key=lambda x: (-x[1], x[0].price or 0))

    return [
        {
            "id": p.id,
            "name": p.name,
            "brand": p.brand,
            "price": p.price,
            "score": score,
            "image_url": p.image_url,
            "dns_url": p.dns_url,
            "wb_url": p.wb_url,
        }
        for p, score in scored[:20]
    ]


def _build_query(category: str, answers: dict, db: Session, model):
    query = db.query(model)

    budget = answers.get("budget")
    if budget is not None:
        query = query.filter(model.price <= float(budget))

    if category == "mouse":
        wireless = answers.get("wireless")
        if wireless == "yes":
            query = query.filter(model.connection_types.contains("Wireless"))
        elif wireless == "no":
            query = query.filter(model.connection_types.contains("USB"))

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
        if use_case == "gaming" and product.refresh_rate_hz is not None and product.refresh_rate_hz >= 144:
            score += 3  # высокая частота обновления важна для игр
        elif use_case == "work" and product.matrix_type == "IPS":
            score += 2  # IPS лучше для цветопередачи при работе

    return score
