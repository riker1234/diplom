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
    assert SUPPORTED_CATEGORIES == {"mouse", "keyboard", "monitor", "headphones", "microphone", "mousepad"}


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


def test_get_questions_headphones_returns_4_questions():
    questions = get_questions("headphones")
    assert len(questions) == 4


def test_get_questions_microphone_returns_3_questions():
    questions = get_questions("microphone")
    assert len(questions) == 3


def test_get_questions_mousepad_returns_4_questions():
    questions = get_questions("mousepad")
    assert len(questions) == 4


def test_headphones_questions_have_required_ids():
    questions = get_questions("headphones")
    ids = [q["id"] for q in questions]
    assert ids == ["use_case", "has_microphone", "connection", "budget"]


def test_microphone_questions_have_required_ids():
    questions = get_questions("microphone")
    ids = [q["id"] for q in questions]
    assert ids == ["use_case", "connection", "budget"]


def test_mousepad_questions_have_required_ids():
    questions = get_questions("mousepad")
    ids = [q["id"] for q in questions]
    assert ids == ["size", "hardness", "rgb", "budget"]


# ── Интеграционные тесты API ──────────────────────────────────────────────────

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

_TEST_DB_URL = "sqlite:///./test_recommendation.db"
_engine = create_engine(_TEST_DB_URL, connect_args={"check_same_thread": False})
_TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
Base.metadata.create_all(bind=_engine)


def _override_get_db():
    db = _TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db
_client = TestClient(app)


def test_questions_endpoint_mouse_returns_3():
    resp = _client.get("/recommend/questions/mouse")
    assert resp.status_code == 200
    data = resp.json()
    assert data["category"] == "mouse"
    assert len(data["questions"]) == 3


def test_questions_endpoint_keyboard_returns_4():
    resp = _client.get("/recommend/questions/keyboard")
    assert resp.status_code == 200
    assert len(resp.json()["questions"]) == 4


def test_questions_endpoint_monitor_returns_3():
    resp = _client.get("/recommend/questions/monitor")
    assert resp.status_code == 200
    assert len(resp.json()["questions"]) == 3


def test_questions_endpoint_unknown_category_404():
    resp = _client.get("/recommend/questions/printer")
    assert resp.status_code == 404


def test_recommend_empty_db_returns_empty_list():
    resp = _client.post(
        "/recommend/",
        json={
            "category": "mouse",
            "answers": {"use_case": "gaming", "wireless": "no", "budget": 3000},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["category"] == "mouse"
    assert data["total"] == 0
    assert data["results"] == []


def test_recommend_unknown_category_404():
    resp = _client.post(
        "/recommend/",
        json={"category": "printer", "answers": {"budget": 1000}},
    )
    assert resp.status_code == 404


def test_recommend_response_shape():
    resp = _client.post(
        "/recommend/",
        json={
            "category": "monitor",
            "answers": {"use_case": "work", "size": "any", "budget": 50000},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "category" in data
    assert "total" in data
    assert "results" in data


def test_questions_endpoint_headphones_returns_4():
    resp = _client.get("/recommend/questions/headphones")
    assert resp.status_code == 200
    assert len(resp.json()["questions"]) == 4


def test_questions_endpoint_microphone_returns_3():
    resp = _client.get("/recommend/questions/microphone")
    assert resp.status_code == 200
    assert len(resp.json()["questions"]) == 3


def test_questions_endpoint_mousepad_returns_4():
    resp = _client.get("/recommend/questions/mousepad")
    assert resp.status_code == 200
    assert len(resp.json()["questions"]) == 4


def test_recommend_headphones_empty_db():
    resp = _client.post(
        "/recommend/",
        json={
            "category": "headphones",
            "answers": {"use_case": "gaming", "has_microphone": "yes", "connection": "wired", "budget": 5000},
        },
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_recommend_microphone_empty_db():
    resp = _client.post(
        "/recommend/",
        json={
            "category": "microphone",
            "answers": {"use_case": "streaming", "connection": "usb", "budget": 8000},
        },
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_recommend_mousepad_empty_db():
    resp = _client.post(
        "/recommend/",
        json={
            "category": "mousepad",
            "answers": {"size": "large", "hardness": "soft", "rgb": "yes", "budget": 2000},
        },
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 0
