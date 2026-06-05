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
    low, _ = scoring.rating_subscore(_p(ozon_rating=5.0, ozon_reviews=3))
    high, _ = scoring.rating_subscore(_p(ozon_rating=4.8, ozon_reviews=900))
    assert low < high
    assert scoring.rating_subscore(_p())[0] == 50.0


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


def test_price_subscore_flagship_prefers_near_budget():
    a = {"budget": 6000, "priority": "flagship"}
    near, _ = scoring.price_subscore(_p(price=5200), a)   # ~87% -> top
    cheap, _ = scoring.price_subscore(_p(price=900), a)   # 15% -> low
    assert near > cheap


def test_price_subscore_zero_budget_is_neutral():
    assert scoring.price_subscore(_p(price=4200), {"budget": 0, "priority": "balance"})[0] == 50.0


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


def test_specs_subscore_mousepad_skips_unknown_rgb():
    sub, _ = scoring.specs_subscore(_p(), "mousepad", {"rgb": "yes"})
    assert sub == 50.0


def test_specs_subscore_microphone_calls_skips_unknown_connection():
    sub, _ = scoring.specs_subscore(_p(), "microphone", {"use_case": "calls"})
    assert sub == 50.0


def test_brand_subscore_from_data():
    import pytest
    brand_avgs = {"logitech": (4.7, 1200), "noname": (4.9, 5)}
    high, lbl = scoring.brand_subscore(_p(brand="Logitech"), brand_avgs)
    assert high == pytest.approx(70.0)  # (4.7-4.0)*100
    assert "4.7" in lbl
    # too few reviews -> neutral, not the inflated 4.9
    low, _ = scoring.brand_subscore(_p(brand="NoName"), brand_avgs)
    assert low == 50.0
    # unknown brand -> neutral
    assert scoring.brand_subscore(_p(brand="Ghost"), brand_avgs)[0] == 50.0


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
