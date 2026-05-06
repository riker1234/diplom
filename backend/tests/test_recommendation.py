import pytest
from pydantic import ValidationError
from app.schemas.recommendation import (
    RecommendRequest,
    RecommendResponse,
    RecommendResultItem,
    QuestionsResponse,
    Question,
    QuestionOption,
)


def test_recommend_request_valid():
    req = RecommendRequest(
        category="mouse",
        answers={"use_case": "gaming", "wireless": "no", "budget": 3000},
    )
    assert req.category == "mouse"
    assert req.answers["budget"] == 3000


def test_recommend_request_missing_category():
    with pytest.raises(ValidationError):
        RecommendRequest(answers={"budget": 1000})


def test_recommend_result_item_valid():
    item = RecommendResultItem(id=1, name="Test Mouse", score=5)
    assert item.score == 5
    assert item.brand is None


def test_questions_response_valid():
    resp = QuestionsResponse(
        category="mouse",
        questions=[
            Question(
                id="use_case",
                text="Для чего используете?",
                type="choice",
                options=[QuestionOption(value="gaming", label="Для игр")],
            )
        ],
    )
    assert resp.category == "mouse"
    assert len(resp.questions) == 1


from app.recommendation.questions import get_questions, SUPPORTED_CATEGORIES


def test_get_questions_mouse_returns_3_questions():
    questions = get_questions("mouse")
    assert len(questions) == 3


def test_get_questions_keyboard_returns_4_questions():
    questions = get_questions("keyboard")
    assert len(questions) == 4


def test_get_questions_monitor_returns_3_questions():
    questions = get_questions("monitor")
    assert len(questions) == 3


def test_get_questions_unknown_returns_none():
    assert get_questions("printer") is None


def test_supported_categories():
    assert SUPPORTED_CATEGORIES == {"mouse", "keyboard", "monitor"}


def test_mouse_questions_have_required_ids():
    questions = get_questions("mouse")
    ids = [q["id"] for q in questions]
    assert ids == ["use_case", "wireless", "budget"]


def test_keyboard_questions_have_required_ids():
    questions = get_questions("keyboard")
    ids = [q["id"] for q in questions]
    assert ids == ["use_case", "form_factor", "switches", "budget"]


def test_monitor_questions_have_required_ids():
    questions = get_questions("monitor")
    ids = [q["id"] for q in questions]
    assert ids == ["use_case", "size", "budget"]


# ── Тесты движка рекомендаций ─────────────────────────────────────────────────

from app.recommendation.engine import _score


class FakeMouse:
    id = 1
    name = "Test Mouse"
    brand = "TestBrand"
    price = 1500.0
    weight_g = 70.0
    connection_types = "USB"
    image_url = None
    dns_url = None
    wb_url = None


class FakeHeavyMouse:
    id = 2
    name = "Heavy Mouse"
    brand = "TestBrand"
    price = 2500.0
    weight_g = 110.0
    connection_types = "USB"
    image_url = None
    dns_url = None
    wb_url = None


class FakeMonitorGaming:
    id = 3
    name = "Gaming Monitor"
    brand = "TestBrand"
    price = 15000.0
    refresh_rate_hz = 144
    matrix_type = "IPS"
    diagonal_inch = 24.0
    image_url = None
    dns_url = None
    wb_url = None


class FakeKeyboard:
    id = 4
    name = "Mech Keyboard"
    brand = "TestBrand"
    price = 3000.0
    switches = "Cherry MX Red"
    form_factor = "TKL"
    image_url = None
    dns_url = None
    wb_url = None


def test_score_gaming_light_mouse_gets_5():
    # +3 за вес ≤80г при use_case=gaming, +2 за цену ≤70% от бюджета
    score = _score(FakeMouse(), "mouse", {"use_case": "gaming", "budget": 3000})
    assert score == 5


def test_score_gaming_heavy_mouse_gets_0():
    # вес >80г — нет бонуса, цена >70% от бюджета — нет бонуса
    score = _score(FakeHeavyMouse(), "mouse", {"use_case": "gaming", "budget": 3000})
    assert score == 0


def test_score_gaming_monitor_gets_5():
    # +3 за частоту ≥144Гц при gaming, +2 за цену ≤70% от бюджета
    score = _score(FakeMonitorGaming(), "monitor", {"use_case": "gaming", "budget": 25000})
    assert score == 5


def test_score_keyboard_linear_gaming_tkl_gets_6():
    # +3 за совпадение переключателей (linear→Red), +1 за gaming+TKL, +2 за цену
    score = _score(
        FakeKeyboard(),
        "keyboard",
        {"use_case": "gaming", "switches": "linear", "budget": 5000},
    )
    assert score == 6


def test_score_no_budget_no_price_bonus():
    # бюджет не указан → ценовой бонус не начисляется
    score = _score(FakeMouse(), "mouse", {"use_case": "gaming"})
    assert score == 3


def test_score_switches_any_no_bonus():
    # switches=any → бонус за переключатели не начисляется
    score = _score(FakeKeyboard(), "keyboard", {"use_case": "gaming", "switches": "any", "budget": 5000})
    assert score == 3
