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
