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
