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


_SWITCH_KEYWORDS: dict[str, list[str]] = {
    "linear": ["Red", "Silver", "Speed", "Yellow", "Black", "линейн", "linear", "Cream", "Amber", "Mute"],
    "tactile": ["Brown", "Clear", "Tactile", "тактильн", "White"],
    "clicky": ["Blue", "Green", "Clicky", "кликающ", "Зелен", "Purple"],
    "magnetic": ["Magnetic", "Hall", "магнитн", "halleffect"],
}


def _specs(product, category: str, answers: dict):
    """Returns (earned, known_max, labels). Normalised by KNOWN criteria only."""
    use_case = answers.get("use_case")
    earned = 0.0
    known_max = 0.0
    labels: list[str] = []

    def crit(known: bool, value: float, mx: float, label: str) -> None:
        nonlocal earned, known_max
        if not known:
            return
        known_max += mx
        earned += value
        if value > 0:
            labels.append(label)

    if category == "mouse":
        w = getattr(product, "weight_g", None)
        if use_case == "office":
            v = 2.0 if (w is not None and 80 <= w <= 130) else (1.0 if w is not None else 0.0)
            crit(w is not None, v, 2.0, f"вес {w} г")
            bc = getattr(product, "button_count", None)
            crit(bc is not None, 1.0 if (bc or 0) > 2 else 0.0, 1.0, f"{bc} кнопок")
        else:  # gaming / both
            if w is not None:
                v = 4.0 if w <= 60 else 3.0 if w <= 80 else 1.0 if w <= 100 else 0.0
                crit(True, v, 4.0, f"вес {w} г")
            dpi = getattr(product, "max_dpi", None)
            if dpi is not None:
                v = 3.0 if dpi >= 25000 else 2.0 if dpi >= 12000 else 1.0 if dpi >= 6000 else 0.0
                crit(True, v, 3.0, f"{dpi} DPI")

    elif category == "keyboard":
        pref = answers.get("switches")
        sw = getattr(product, "switches", None)
        if pref and pref != "any" and sw is not None:
            kws = _SWITCH_KEYWORDS.get(pref, [])
            match = any(kw.lower() in sw.lower() for kw in kws)
            crit(True, 3.0 if match else 0.0, 3.0, f"переключатели {sw}")
        ff = getattr(product, "form_factor", None)
        if use_case == "gaming" and ff is not None:
            match = any(k in ff.lower() for k in ("tkl", "полноразмерная"))
            crit(True, 1.0 if match else 0.0, 1.0, f"форм-фактор {ff}")
        km = getattr(product, "keycap_material", None)
        if km is not None:
            crit(True, 1.0 if "pbt" in km.lower() else 0.0, 1.0, f"колпачки {km}")

    elif category == "monitor":
        hz = getattr(product, "refresh_rate_hz", None)
        mt = getattr(product, "matrix_type", None)
        res = getattr(product, "resolution", None)
        rt = getattr(product, "response_time_ms", None)
        if use_case == "gaming":
            if hz is not None:
                v = 6.0 if hz >= 360 else 5.0 if hz >= 240 else 4.0 if hz >= 165 else 3.0 if hz >= 144 else 0.0
                crit(True, v, 6.0, f"{hz} Гц")
            if rt is not None:
                crit(True, 2.0 if rt <= 1 else 1.0 if rt <= 4 else 0.0, 2.0, f"отклик {rt} мс")
        elif use_case == "work":
            if mt is not None:
                crit(True, 3.0 if "ips" in mt.lower() else 0.0, 3.0, f"матрица {mt}")
            if res is not None:
                crit(True, 2.0 if "3840" in res else 0.0, 2.0, f"разрешение {res}")
        else:  # both
            if mt is not None:
                crit(True, 2.0 if "ips" in mt.lower() else 0.0, 2.0, f"матрица {mt}")
            if hz is not None:
                crit(True, 2.0 if hz >= 144 else 0.0, 2.0, f"{hz} Гц")

    elif category == "headphones":
        mic = getattr(product, "has_microphone", None)
        if use_case in ("gaming", "calls"):
            crit(mic is not None, 2.0 if mic else 0.0, 2.0, "микрофон есть")
        elif use_case == "music":
            crit(mic is not None, 1.0 if not mic else 0.0, 1.0, "без микрофона")
        imp = getattr(product, "impedance_ohm", None)
        if imp is not None:
            crit(True, 1.0 if imp <= 64 else 0.0, 1.0, f"импеданс {imp} Ом")

    elif category == "microphone":
        mtp = getattr(product, "mic_type", None)
        dirn = getattr(product, "directionality", None)
        if use_case in ("streaming", "recording"):
            if mtp is not None:
                crit(True, 2.0 if "конденсат" in mtp.lower() else 0.0, 2.0, f"тип {mtp}")
            if dirn is not None:
                crit(True, 1.0 if "кардио" in dirn.lower() else 0.0, 1.0, f"направленность {dirn}")
        elif use_case == "calls":
            iface = (getattr(product, "interface", "") or "") + " " + (getattr(product, "connection_types", "") or "")
            crit(bool(iface.strip()), 2.0 if "usb" in iface.lower() else 0.0, 2.0, "USB plug & play")

    elif category == "mousepad":
        rgb_pref = answers.get("rgb")
        rgb = getattr(product, "has_rgb", None)
        if rgb_pref == "yes":
            crit(rgb is not None, 2.0 if rgb else 0.0, 2.0, "RGB есть")
        elif rgb_pref == "no":
            crit(rgb is not None, 1.0 if not rgb else 0.0, 1.0, "без RGB")

    return earned, known_max, labels


def specs_subscore(product, category: str, answers: dict) -> tuple[float, str]:
    earned, known_max, labels = _specs(product, category, answers)
    if known_max <= 0:
        return 50.0, "нет данных по ТТХ"
    sub = _clamp(earned / known_max * 100.0)
    return sub, ", ".join(labels) if labels else "ТТХ ниже нормы"
