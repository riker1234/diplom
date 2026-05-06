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
