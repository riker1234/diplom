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


class FakeHeadphonesWithMic:
    id = 5
    name = "Gaming Headset"
    brand = "TestBrand"
    price = 2000.0
    has_microphone = True
    connection_types = "USB"
    construction_type = "накладные"
    noise_cancellation = None
    image_url = None
    dns_url = None
    wb_url = None


class FakeHeadphonesNoMic:
    id = 6
    name = "Music Headphones"
    brand = "TestBrand"
    price = 3000.0
    has_microphone = False
    connection_types = "3.5 мм"
    construction_type = "накладные"
    noise_cancellation = None
    image_url = None
    dns_url = None
    wb_url = None


class FakeMicrophone:
    id = 7
    name = "USB Mic"
    brand = "TestBrand"
    price = 4000.0
    mic_type = "конденсаторный"
    connection_types = "USB"
    directionality = "кардиоида"
    frequency_range = "20-20000 Гц"
    image_url = None
    dns_url = None
    wb_url = None


class FakeMousepad:
    id = 8
    name = "RGB Mousepad"
    brand = "TestBrand"
    price = 1500.0
    has_rgb = True
    hardness = "мягкий"
    size = "XL"
    surface_material = "ткань"
    image_url = None
    dns_url = None
    wb_url = None


def test_score_headphones_gaming_with_mic_gets_bonus():
    # +2 за наличие микрофона при use_case=gaming, +2 за цену ≤70% от бюджета
    score = _score(FakeHeadphonesWithMic(), "headphones", {"use_case": "gaming", "budget": 4000})
    assert score == 4


def test_score_headphones_music_no_mic_gets_bonus():
    # +1 за отсутствие микрофона при use_case=music
    score = _score(FakeHeadphonesNoMic(), "headphones", {"use_case": "music", "budget": 5000})
    assert score == 3


def test_score_headphones_calls_needs_mic():
    # +3 за микрофон при use_case=calls
    score = _score(FakeHeadphonesWithMic(), "headphones", {"use_case": "calls", "budget": 4000})
    assert score == 5


def test_score_microphone_streaming_condenser():
    # +2 за конденсаторный микрофон для стриминга, +2 за цену ≤70% от бюджета
    score = _score(FakeMicrophone(), "microphone", {"use_case": "streaming", "budget": 8000})
    assert score == 4


def test_score_mousepad_rgb_gets_bonus():
    # +1 за RGB, +2 за цену ≤70% от бюджета
    score = _score(FakeMousepad(), "mousepad", {"budget": 3000})
    assert score == 3


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
