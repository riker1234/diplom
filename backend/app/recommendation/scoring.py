"""Pure scoring functions for the recommendation engine (no DB access).

Score model: final 0-100 = weighted sum of four 0-100 sub-scores
(specs, rating, brand, price). See
docs/superpowers/specs/2026-06-04-scoring-rework-design.md
"""

RATING_M = 50.0      # confidence constant for Bayesian shrinkage
RATING_C = 4.3       # prior mean (typical marketplace average)
RATING_FLOOR = 4.0   # ratings below this map to 0
BRAND_MIN_REVIEWS = 30  # min total reviews for a brand average to be trusted


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def best_price(product) -> float | None:
    prices = [p for p in (product.price, product.wb_price, product.citilink_price)
              if p is not None]
    return min(prices) if prices else None


def representative_rating(product) -> tuple[float | None, int | None]:
    """Rating from the source with the most reviews."""
    candidates = [
        (getattr(product, "ozon_rating", None), getattr(product, "ozon_reviews", None)),
        (getattr(product, "citilink_rating", None), getattr(product, "citilink_reviews", None)),
        (getattr(product, "wb_rating", None), getattr(product, "wb_reviews", None)),
    ]
    best = None
    for rt, rv in candidates:
        if rt is None:
            continue
        rv = rv or 0
        if best is None or rv > best[1]:
            best = (rt, rv)
    return (best[0], best[1]) if best else (None, None)


def rating_subscore(product) -> tuple[float, str]:
    r, v = representative_rating(product)
    if r is None or not v:
        return 50.0, "нет отзывов"
    adj = r * v / (v + RATING_M) + RATING_C * RATING_M / (v + RATING_M)
    sub = _clamp((adj - RATING_FLOOR) * 100.0)
    return sub, f"{r:.1f} · {v} отз."


def _balance_curve(ratio: float) -> float:
    if ratio < 0.15:
        return 20.0
    if ratio <= 0.50:
        return 20.0 + (ratio - 0.15) / 0.35 * 80.0   # 20 -> 100
    if ratio <= 0.75:
        return 100.0
    if ratio <= 1.0:
        return 100.0 - (ratio - 0.75) / 0.25 * 50.0   # 100 -> 50
    return 50.0


def _budget_curve(ratio: float) -> float:
    if ratio <= 0.50:
        return 100.0
    if ratio <= 1.0:
        return 100.0 - (ratio - 0.50) / 0.50 * 70.0   # 100 -> 30
    return 30.0


def _flagship_curve(ratio: float) -> float:
    if ratio < 0.40:
        return max(10.0, ratio / 0.40 * 40.0)  # flat floor 10 below ~10% of budget, then up to 40
    if ratio < 0.75:
        return 40.0 + (ratio - 0.40) / 0.35 * 60.0    # 40 -> 100
    return 100.0


def price_subscore(product, answers: dict) -> tuple[float, str]:
    budget = answers.get("budget")
    bp = best_price(product)
    if budget is None or float(budget) <= 0 or bp is None:
        return 50.0, "бюджет не задан"
    ratio = bp / float(budget)
    priority = answers.get("priority", "balance")
    if priority == "budget":
        sub = _budget_curve(ratio)
    elif priority == "flagship":
        sub = _flagship_curve(ratio)
    else:
        sub = _balance_curve(ratio)
    return _clamp(sub), f"{int(ratio * 100)}% бюджета"
