# Переработка скоринга СППР — план реализации

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Заменить «сырую» сумму баллов в движке рекомендаций на интерпретируемую шкалу 0–100 из 4 взвешенных под-оценок (характеристики, рейтинг, бренд-из-данных, соответствие бюджету).

**Architecture:** Чистые функции скоринга выносятся в новый модуль `app/recommendation/scoring.py` (легко юнит-тестировать без БД). `engine.py` остаётся оркестратором: строит выборку (`_build_query` — без изменений), считает средние рейтинги брендов из БД и вызывает `scoring.score_product`. Контракт ответа (`score`, `score_breakdown`) сохраняется, фронт не меняется.

**Tech Stack:** Python 3.11, SQLAlchemy 2.0 (sync), pytest. Спека: `docs/superpowers/specs/2026-06-04-scoring-rework-design.md`.

---

## Файловая структура

- **Create** `backend/app/recommendation/scoring.py` — чистые функции: `best_price`, `representative_rating`, `rating_subscore`, `price_subscore`, `specs_subscore`, `brand_subscore`, `WEIGHTS`, `score_product`. Никакого доступа к БД.
- **Create** `backend/tests/test_scoring.py` — юнит-тесты под-оценок + регрессионный кейс Razer.
- **Modify** `backend/app/recommendation/engine.py` — `recommend()` вызывает `scoring.score_product`; добавляется `_compute_brand_avgs`; удаляются `_BRAND_TIER`, `_brand_score`, `_score`, `_SWITCH_KEYWORDS` (переезжает в scoring), `_best_price` (переезжает в scoring). `_build_query`, `_MIN_PRICE_RATIO`, `_parse_max_dim`, `_filter_mousepad_size` остаются.

Константы (в `scoring.py`): `RATING_M = 50.0`, `RATING_C = 4.3`, `RATING_FLOOR = 4.0`, `BRAND_MIN_REVIEWS = 30`.

---

## Task 1: Каркас scoring.py — цена, представительный рейтинг, под-оценка рейтинга

**Files:**
- Create: `backend/app/recommendation/scoring.py`
- Test: `backend/tests/test_scoring.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_scoring.py
from types import SimpleNamespace
from app.recommendation import scoring


def _p(**kw):
    base = dict(price=None, wb_price=None, citilink_price=None,
               ozon_rating=None, ozon_reviews=None,
               citilink_rating=None, citilink_reviews=None,
               wb_rating=None, wb_reviews=None)
    base.update(kw)
    return SimpleNamespace(**base)


def test_best_price_picks_min():
    assert scoring.best_price(_p(price=5500, wb_price=4200, citilink_price=None)) == 4200
    assert scoring.best_price(_p()) is None


def test_representative_rating_picks_source_with_most_reviews():
    p = _p(ozon_rating=4.4, ozon_reviews=1600, wb_rating=4.9, wb_reviews=10)
    assert scoring.representative_rating(p) == (4.4, 1600)
    assert scoring.representative_rating(_p()) == (None, None)


def test_rating_subscore_shrinks_low_review_counts():
    # 5.0 from 3 reviews must NOT score near the top
    low, _ = scoring.rating_subscore(_p(ozon_rating=5.0, ozon_reviews=3))
    high, _ = scoring.rating_subscore(_p(ozon_rating=4.8, ozon_reviews=900))
    assert low < high
    assert scoring.rating_subscore(_p())[0] == 50.0  # no reviews -> neutral
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_scoring.py -v`
Expected: FAIL with `ModuleNotFoundError`/`AttributeError` (scoring not defined).

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/recommendation/scoring.py
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_scoring.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add backend/app/recommendation/scoring.py backend/tests/test_scoring.py
git commit -m "feat(scoring): rating sub-score with review-count shrinkage"
```

---

## Task 2: Под-оценка соответствия бюджету

**Files:**
- Modify: `backend/app/recommendation/scoring.py`
- Test: `backend/tests/test_scoring.py`

- [ ] **Step 1: Write the failing test**

```python
# append to backend/tests/test_scoring.py
def test_price_subscore_balance_peaks_in_midrange():
    a = {"budget": 6000, "priority": "balance"}
    mid, _ = scoring.price_subscore(_p(price=4200), a)   # 70% -> peak
    high, _ = scoring.price_subscore(_p(price=5800), a)  # 97% -> tapered
    cheap, _ = scoring.price_subscore(_p(price=600), a)  # 10% -> penalised
    assert mid == 100.0
    assert high < mid and cheap < mid


def test_price_subscore_budget_prefers_cheap():
    a = {"budget": 6000, "priority": "budget"}
    cheap, _ = scoring.price_subscore(_p(price=1500), a)
    pricey, _ = scoring.price_subscore(_p(price=5800), a)
    assert cheap > pricey


def test_price_subscore_neutral_without_budget():
    assert scoring.price_subscore(_p(price=4200), {"priority": "balance"})[0] == 50.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_scoring.py -k price -v`
Expected: FAIL with `AttributeError: module ... has no attribute 'price_subscore'`.

- [ ] **Step 3: Write minimal implementation**

```python
# append to backend/app/recommendation/scoring.py
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
        return max(10.0, ratio / 0.40 * 40.0)         # up to 40
    if ratio < 0.75:
        return 40.0 + (ratio - 0.40) / 0.35 * 60.0    # 40 -> 100
    return 100.0


def price_subscore(product, answers: dict) -> tuple[float, str]:
    budget = answers.get("budget")
    bp = best_price(product)
    if budget is None or bp is None:
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_scoring.py -k price -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/recommendation/scoring.py backend/tests/test_scoring.py
git commit -m "feat(scoring): price-fit sub-score curves per priority"
```

---

## Task 3: Под-оценка характеристик (нормировка по известным критериям)

**Files:**
- Modify: `backend/app/recommendation/scoring.py`
- Test: `backend/tests/test_scoring.py`

- [ ] **Step 1: Write the failing test**

```python
# append to backend/tests/test_scoring.py
def test_specs_subscore_mouse_gaming_full_marks():
    p = _p(weight_g=58, max_dpi=30000)
    sub, label = scoring.specs_subscore(p, "mouse", {"use_case": "gaming"})
    assert sub == 100.0
    assert "58" in label


def test_specs_subscore_normalises_over_known_only():
    # only weight known -> not penalised for missing dpi
    p = _p(weight_g=58, max_dpi=None)
    sub, _ = scoring.specs_subscore(p, "mouse", {"use_case": "gaming"})
    assert sub == 100.0


def test_specs_subscore_neutral_when_no_data():
    sub, _ = scoring.specs_subscore(_p(), "mouse", {"use_case": "gaming"})
    assert sub == 50.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_scoring.py -k specs -v`
Expected: FAIL (`specs_subscore` not defined).

- [ ] **Step 3: Write minimal implementation**

```python
# append to backend/app/recommendation/scoring.py
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
        w = product.weight_g
        if use_case == "office":
            v = 2.0 if (w is not None and 80 <= w <= 130) else (1.0 if w is not None else 0.0)
            crit(w is not None, v, 2.0, f"вес {w} г")
            bc = product.button_count
            crit(bc is not None, 1.0 if (bc or 0) > 2 else 0.0, 1.0, f"{bc} кнопок")
        else:  # gaming / both
            if w is not None:
                v = 4.0 if w <= 60 else 3.0 if w <= 80 else 1.0 if w <= 100 else 0.0
                crit(True, v, 4.0, f"вес {w} г")
            dpi = product.max_dpi
            if dpi is not None:
                v = 3.0 if dpi >= 25000 else 2.0 if dpi >= 12000 else 1.0 if dpi >= 6000 else 0.0
                crit(True, v, 3.0, f"{dpi} DPI")

    elif category == "keyboard":
        pref = answers.get("switches")
        sw = product.switches
        if pref and pref != "any" and sw is not None:
            kws = _SWITCH_KEYWORDS.get(pref, [])
            match = any(kw.lower() in sw.lower() for kw in kws)
            crit(True, 3.0 if match else 0.0, 3.0, f"переключатели {sw}")
        ff = product.form_factor
        if use_case == "gaming" and ff is not None:
            match = any(k in ff.lower() for k in ("tkl", "полноразмерная", "full"))
            crit(True, 1.0 if match else 0.0, 1.0, f"форм-фактор {ff}")
        km = getattr(product, "keycap_material", None)
        if km is not None:
            crit(True, 1.0 if "pbt" in km.lower() else 0.0, 1.0, f"колпачки {km}")

    elif category == "monitor":
        hz = product.refresh_rate_hz
        mt = product.matrix_type
        res = product.resolution
        rt = product.response_time_ms
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
        mic = product.has_microphone
        if use_case in ("gaming", "calls"):
            crit(mic is not None, 2.0 if mic else 0.0, 2.0, "микрофон есть")
        elif use_case == "music":
            crit(mic is not None, 1.0 if not mic else 0.0, 1.0, "без микрофона")
        imp = product.impedance_ohm
        if imp is not None:
            crit(True, 1.0 if imp <= 64 else 0.0, 1.0, f"импеданс {imp} Ом")

    elif category == "microphone":
        mtp = product.mic_type
        dirn = product.directionality
        if use_case in ("streaming", "recording"):
            if mtp is not None:
                crit(True, 2.0 if "конденсат" in mtp.lower() else 0.0, 2.0, f"тип {mtp}")
            if dirn is not None:
                crit(True, 1.0 if "кардио" in dirn.lower() else 0.0, 1.0, f"направленность {dirn}")
        elif use_case == "calls":
            iface = (getattr(product, "interface", "") or "") + " " + (product.connection_types or "")
            crit(True, 2.0 if "usb" in iface.lower() else 0.0, 2.0, "USB plug & play")

    elif category == "mousepad":
        rgb_pref = answers.get("rgb")
        rgb = product.has_rgb
        if rgb_pref == "yes":
            crit(True, 2.0 if rgb else 0.0, 2.0, "RGB есть")
        elif rgb_pref == "no":
            crit(True, 1.0 if not rgb else 0.0, 1.0, "без RGB")

    return earned, known_max, labels


def specs_subscore(product, category: str, answers: dict) -> tuple[float, str]:
    earned, known_max, labels = _specs(product, category, answers)
    if known_max <= 0:
        return 50.0, "нет данных по ТТХ"
    sub = _clamp(earned / known_max * 100.0)
    return sub, ", ".join(labels) if labels else "ТТХ ниже нормы"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_scoring.py -k specs -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/recommendation/scoring.py backend/tests/test_scoring.py
git commit -m "feat(scoring): specs sub-score normalised by known criteria"
```

---

## Task 4: Под-оценка бренда (из переданных средних)

**Files:**
- Modify: `backend/app/recommendation/scoring.py`
- Test: `backend/tests/test_scoring.py`

- [ ] **Step 1: Write the failing test**

```python
# append to backend/tests/test_scoring.py
def test_brand_subscore_from_data():
    brand_avgs = {"logitech": (4.7, 1200), "noname": (4.9, 5)}
    high, lbl = scoring.brand_subscore(_p(brand="Logitech"), brand_avgs)
    assert high == 70.0  # (4.7-4.0)*100
    assert "4.7" in lbl
    # too few reviews -> neutral, not the inflated 4.9
    low, _ = scoring.brand_subscore(_p(brand="NoName"), brand_avgs)
    assert low == 50.0
    # unknown brand -> neutral
    assert scoring.brand_subscore(_p(brand="Ghost"), brand_avgs)[0] == 50.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_scoring.py -k brand -v`
Expected: FAIL (`brand_subscore` not defined).

- [ ] **Step 3: Write minimal implementation**

```python
# append to backend/app/recommendation/scoring.py
def brand_subscore(product, brand_avgs: dict) -> tuple[float, str]:
    """brand_avgs: {brand_lower: (avg_rating, total_reviews)} for the category."""
    name = (product.brand or "").strip()
    key = name.lower()
    entry = brand_avgs.get(key)
    if not entry or entry[1] < BRAND_MIN_REVIEWS:
        return 50.0, f"{name or 'бренд'}: мало данных"
    avg, _total = entry
    return _clamp((avg - RATING_FLOOR) * 100.0), f"{name}: ср. {avg:.1f}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_scoring.py -k brand -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/recommendation/scoring.py backend/tests/test_scoring.py
git commit -m "feat(scoring): data-driven brand sub-score"
```

---

## Task 5: Веса + сборка итогового балла (+ регрессия Razer)

**Files:**
- Modify: `backend/app/recommendation/scoring.py`
- Test: `backend/tests/test_scoring.py`

- [ ] **Step 1: Write the failing test**

```python
# append to backend/tests/test_scoring.py
def test_score_product_razer_loses_to_higher_rated_midbrand():
    answers = {"use_case": "gaming", "priority": "balance", "budget": 6000}
    brand_avgs = {"razer": (4.5, 5000), "midbrand": (4.6, 3000)}
    razer = _p(brand="Razer", price=5500, weight_g=58, max_dpi=30000,
               ozon_rating=4.4, ozon_reviews=1600)
    mid = _p(brand="MidBrand", price=4200, weight_g=55, max_dpi=26000,
             ozon_rating=4.8, ozon_reviews=900)
    s_razer, br_razer = scoring.score_product(razer, "mouse", answers, brand_avgs)
    s_mid, _ = scoring.score_product(mid, "mouse", answers, brand_avgs)
    assert 0 <= s_razer <= 100 and 0 <= s_mid <= 100
    assert s_mid > s_razer
    assert len(br_razer) == 4  # one breakdown item per component


def test_weights_sum_to_one():
    for w in scoring.WEIGHTS.values():
        assert abs(sum(w.values()) - 1.0) < 1e-9
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_scoring.py -k "score_product or weights" -v`
Expected: FAIL (`WEIGHTS`/`score_product` not defined).

- [ ] **Step 3: Write minimal implementation**

```python
# append to backend/app/recommendation/scoring.py
WEIGHTS: dict[str, dict[str, float]] = {
    "budget":   {"specs": 0.30, "rating": 0.30, "brand": 0.05, "price": 0.35},
    "balance":  {"specs": 0.40, "rating": 0.30, "brand": 0.12, "price": 0.18},
    "flagship": {"specs": 0.45, "rating": 0.20, "brand": 0.20, "price": 0.15},
}


def score_product(product, category: str, answers: dict,
                  brand_avgs: dict) -> tuple[int, list[dict]]:
    priority = answers.get("priority", "balance")
    w = WEIGHTS.get(priority, WEIGHTS["balance"])

    specs, specs_lbl = specs_subscore(product, category, answers)
    rating, rating_lbl = rating_subscore(product)
    brand, brand_lbl = brand_subscore(product, brand_avgs)
    price, price_lbl = price_subscore(product, answers)

    parts = [
        ("ТТХ", specs, w["specs"], specs_lbl),
        ("Рейтинг", rating, w["rating"], rating_lbl),
        ("Бренд", brand, w["brand"], brand_lbl),
        ("Цена", price, w["price"], price_lbl),
    ]

    total = 0.0
    breakdown: list[dict] = []
    for name, sub, weight, lbl in parts:
        contrib = sub * weight
        total += contrib
        pts = round(contrib)
        breakdown.append({
            "label": f"{name} — {lbl}",
            "points": pts,
            "positive": pts >= 0,
        })
    return round(total), breakdown
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_scoring.py -v`
Expected: PASS (all tests).

- [ ] **Step 5: Commit**

```bash
git add backend/app/recommendation/scoring.py backend/tests/test_scoring.py
git commit -m "feat(scoring): weighted 0-100 combination + Razer regression test"
```

---

## Task 6: Подключить scoring в engine.py; убрать старый код

**Files:**
- Modify: `backend/app/recommendation/engine.py`
- Test: `backend/tests/test_api.py` (регрессия), `backend/tests/test_scoring.py`

- [ ] **Step 1: Write the failing test**

```python
# append to backend/tests/test_scoring.py
def test_compute_brand_avgs_weights_by_reviews():
    from types import SimpleNamespace
    from app.recommendation.engine import _compute_brand_avgs

    class FakeQuery:
        def __init__(self, rows): self._rows = rows
        def all(self): return self._rows

    class FakeDB:
        def __init__(self, rows): self._rows = rows
        def query(self, _model): return FakeQuery(self._rows)

    def row(brand, rt, rv):
        return SimpleNamespace(brand=brand, price=1000, wb_price=None, citilink_price=None,
                               ozon_rating=rt, ozon_reviews=rv,
                               citilink_rating=None, citilink_reviews=None,
                               wb_rating=None, wb_reviews=None)

    db = FakeDB([row("Logi", 4.8, 100), row("Logi", 4.0, 100), row("X", 5.0, 2)])
    avgs = _compute_brand_avgs(db, model=object())
    assert abs(avgs["logi"][0] - 4.4) < 1e-6   # (4.8*100 + 4.0*100)/200
    assert avgs["logi"][1] == 200
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_scoring.py -k compute_brand -v`
Expected: FAIL (`_compute_brand_avgs` not defined).

- [ ] **Step 3: Rewrite engine.py scoring path**

In `backend/app/recommendation/engine.py`:

(a) Replace the top imports block (lines 1-9) — add scoring import:

```python
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
```

(b) DELETE these now-unused blocks entirely: `_SWITCH_KEYWORDS` (moved to scoring), `_BRAND_TIER` dict, `_brand_score()`, the old `_best_price()` def, and the whole `_score()` function. KEEP `_MODEL_MAP`, `_MIN_PRICE_RATIO`, `_parse_max_dim`, `_filter_mousepad_size`, `_build_query`.

(c) Add the brand-averages helper (anywhere above `recommend`):

```python
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
```

(d) Replace the scoring + sort section inside `recommend()` (the `scored = [...]` comprehension and the priority sort) with:

```python
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
```

The `return [ {...} for p, score, breakdown in scored[:20] ]` block stays unchanged (it already emits `score` and `score_breakdown`).

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd backend && python -m pytest tests/ -v`
Expected: PASS — `test_scoring.py` all green, `test_api.py` / `test_models.py` still pass (recommendation endpoints return `score` in 0–100 with 4-item `score_breakdown`).

- [ ] **Step 5: Sanity-check against a real category (manual)**

Run:
```bash
cd backend && python -c "from app.database import SessionLocal; from app.recommendation.engine import recommend; db=SessionLocal(); r=recommend('mouse', {'use_case':'gaming','priority':'balance','budget':6000}, db); [print(round(x['score']), x['name'][:40]) for x in r[:5]]; db.close()"
```
Expected: 5 mice printed, scores in 0–100, ordered descending, вменяемый топ.

- [ ] **Step 6: Commit**

```bash
git add backend/app/recommendation/engine.py backend/tests/test_scoring.py
git commit -m "feat(engine): switch recommend() to weighted 0-100 scoring"
```

---

## Self-Review

- **Spec coverage:** §3.1 веса → Task 5 (`WEIGHTS`). §3.2 ТТХ → Task 3 (`specs_subscore`, нормировка по известным + углубления). §3.3 рейтинг → Task 1. §3.4 бренд-из-данных → Task 4 (`brand_subscore`) + Task 6 (`_compute_brand_avgs`). §3.5 цена → Task 2. §4 сортировка/breakdown → Task 5 (4 элемента) + Task 6 (sort, return). §5 пропуски → нейтрал 50 во всех под-оценках (Tasks 1–4). §6 пример Razer → Task 5 регрессионный тест. §7 non-goals: `_build_query`/анкета/`setup_engine`/фронт не трогаются (Task 6 (b) сохраняет `_build_query`). §8 тесты → Tasks 1–6.
- **Placeholder scan:** код полный в каждом шаге, плейсхолдеров нет.
- **Type consistency:** `score_product(product, category, answers, brand_avgs)`, `brand_subscore(product, brand_avgs)`, `representative_rating`/`best_price` — сигнатуры совпадают между scoring.py и вызовами в engine.py; `brand_avgs` формат `{brand_lower: (avg, total_reviews)}` одинаков в `_compute_brand_avgs` (Task 6) и `brand_subscore` (Task 4).
