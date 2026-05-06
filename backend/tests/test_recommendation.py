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
