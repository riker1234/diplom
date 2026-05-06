# Recommendation Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a questionnaire-based recommendation engine that accepts user answers and returns a relevance-scored list of peripheral products from the database.

**Architecture:** Config-driven approach — questionnaire definitions live in `questions.py` as plain Python dicts, `engine.py` translates answers into SQLAlchemy hard filters and calculates a relevance score per product, a FastAPI router exposes two endpoints (`GET /recommend/questions/{category}` and `POST /recommend/`).

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Pydantic 2.x, pytest + httpx (TestClient), SQLite for tests.

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `app/schemas/recommendation.py` | Pydantic schemas for request/response |
| Create | `app/recommendation/questions.py` | Questionnaire definitions for 3 categories |
| Create | `app/recommendation/engine.py` | Hard filter builder + relevance scorer |
| Create | `app/routers/recommendation.py` | FastAPI router, 2 endpoints |
| Modify | `app/main.py` | Register recommendation router |
| Create | `tests/test_recommendation.py` | All tests for this module |

---

## Task 1: Pydantic Schemas

**Files:**
- Create: `backend/app/schemas/recommendation.py`
- Create: `backend/tests/test_recommendation.py`

- [ ] **Step 1.1: Write failing tests for schemas**

Create `backend/tests/test_recommendation.py`:

```python
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
```

- [ ] **Step 1.2: Run to confirm FAIL**

```
cd backend
pytest tests/test_recommendation.py -v
```

Expected: `ImportError: cannot import name 'RecommendRequest'`

- [ ] **Step 1.3: Create schemas file**

Create `backend/app/schemas/recommendation.py`:

```python
from pydantic import BaseModel
from typing import Optional


class RecommendRequest(BaseModel):
    category: str
    answers: dict[str, str | int | float]


class RecommendResultItem(BaseModel):
    id: int
    name: str
    brand: Optional[str] = None
    price: Optional[float] = None
    score: int
    image_url: Optional[str] = None
    dns_url: Optional[str] = None
    wb_url: Optional[str] = None

    model_config = {"from_attributes": True}


class RecommendResponse(BaseModel):
    category: str
    total: int
    results: list[RecommendResultItem]


class QuestionOption(BaseModel):
    value: str
    label: str


class Question(BaseModel):
    id: str
    text: str
    type: str
    options: Optional[list[QuestionOption]] = None
    placeholder: Optional[str] = None


class QuestionsResponse(BaseModel):
    category: str
    questions: list[Question]
```

- [ ] **Step 1.4: Run to confirm PASS**

```
cd backend
pytest tests/test_recommendation.py -v
```

Expected: 4 passed

- [ ] **Step 1.5: Commit**

```
git add backend/app/schemas/recommendation.py backend/tests/test_recommendation.py
git commit -m "feat: add recommendation pydantic schemas"
```

---

## Task 2: Questions Config

**Files:**
- Modify: `backend/app/recommendation/questions.py`
- Modify: `backend/tests/test_recommendation.py` (append tests)

- [ ] **Step 2.1: Append failing tests**

Add to the bottom of `backend/tests/test_recommendation.py`:

```python
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
```

- [ ] **Step 2.2: Run to confirm FAIL**

```
cd backend
pytest tests/test_recommendation.py -v
```

Expected: `ImportError: cannot import name 'get_questions'`

- [ ] **Step 2.3: Implement questions.py**

Create `backend/app/recommendation/questions.py`:

```python
QUESTIONS: dict[str, list[dict]] = {
    "mouse": [
        {
            "id": "use_case",
            "text": "Для чего используете мышь?",
            "type": "choice",
            "options": [
                {"value": "gaming", "label": "Для игр"},
                {"value": "office", "label": "Для работы"},
                {"value": "both", "label": "Для всего"},
            ],
        },
        {
            "id": "wireless",
            "text": "Нужна беспроводная?",
            "type": "choice",
            "options": [
                {"value": "yes", "label": "Да"},
                {"value": "no", "label": "Нет, проводная"},
                {"value": "any", "label": "Не важно"},
            ],
        },
        {
            "id": "budget",
            "text": "Максимальный бюджет (₽)?",
            "type": "number",
            "placeholder": "Например: 3000",
        },
    ],
    "keyboard": [
        {
            "id": "use_case",
            "text": "Для чего используете клавиатуру?",
            "type": "choice",
            "options": [
                {"value": "gaming", "label": "Для игр"},
                {"value": "typing", "label": "Для печати"},
                {"value": "both", "label": "Для всего"},
            ],
        },
        {
            "id": "form_factor",
            "text": "Форм-фактор?",
            "type": "choice",
            "options": [
                {"value": "full", "label": "Полноразмерная (Full)"},
                {"value": "tkl", "label": "Без цифрового блока (TKL)"},
                {"value": "compact", "label": "Компактная (60–75%)"},
                {"value": "any", "label": "Не важно"},
            ],
        },
        {
            "id": "switches",
            "text": "Тип переключателей?",
            "type": "choice",
            "options": [
                {"value": "linear", "label": "Линейные (тихие, плавные)"},
                {"value": "tactile", "label": "Тактильные (с ощущением клика)"},
                {"value": "clicky", "label": "Кликающие (громкие)"},
                {"value": "any", "label": "Не важно"},
            ],
        },
        {
            "id": "budget",
            "text": "Максимальный бюджет (₽)?",
            "type": "number",
            "placeholder": "Например: 5000",
        },
    ],
    "monitor": [
        {
            "id": "use_case",
            "text": "Основное использование?",
            "type": "choice",
            "options": [
                {"value": "gaming", "label": "Игры"},
                {"value": "work", "label": "Работа и учёба"},
                {"value": "both", "label": "Всё понемногу"},
            ],
        },
        {
            "id": "size",
            "text": "Размер экрана?",
            "type": "choice",
            "options": [
                {"value": "small", "label": "До 24\""},
                {"value": "medium", "label": "24–27\""},
                {"value": "large", "label": "27\" и больше"},
                {"value": "any", "label": "Не важно"},
            ],
        },
        {
            "id": "budget",
            "text": "Максимальный бюджет (₽)?",
            "type": "number",
            "placeholder": "Например: 20000",
        },
    ],
}

SUPPORTED_CATEGORIES: set[str] = set(QUESTIONS.keys())


def get_questions(category: str) -> list[dict] | None:
    return QUESTIONS.get(category)
```

- [ ] **Step 2.4: Run to confirm PASS**

```
cd backend
pytest tests/test_recommendation.py -v
```

Expected: 13 passed

- [ ] **Step 2.5: Commit**

```
git add backend/app/recommendation/questions.py backend/tests/test_recommendation.py
git commit -m "feat: add recommendation questionnaire config for 3 categories"
```

---

## Task 3: Engine — Filter Builder + Scorer

**Files:**
- Create: `backend/app/recommendation/engine.py`
- Modify: `backend/tests/test_recommendation.py` (append tests)

- [ ] **Step 3.1: Append scoring tests**

Add to `backend/tests/test_recommendation.py`:

```python
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
    # +3 (weight<=80 gaming) +2 (price<=70% of budget 3000)
    score = _score(FakeMouse(), "mouse", {"use_case": "gaming", "budget": 3000})
    assert score == 5


def test_score_gaming_heavy_mouse_gets_0():
    # weight>80, price>70% of budget
    score = _score(FakeHeavyMouse(), "mouse", {"use_case": "gaming", "budget": 3000})
    assert score == 0


def test_score_gaming_monitor_gets_5():
    # +3 (refresh>=144 gaming) +2 (price<=70% of 25000)
    score = _score(FakeMonitorGaming(), "monitor", {"use_case": "gaming", "budget": 25000})
    assert score == 5


def test_score_keyboard_linear_gaming_tkl_gets_6():
    # +3 (switches match linear: "Red") +1 (gaming TKL) +2 (price<=70% of 5000)
    score = _score(
        FakeKeyboard(),
        "keyboard",
        {"use_case": "gaming", "switches": "linear", "budget": 5000},
    )
    assert score == 6


def test_score_no_budget_no_price_bonus():
    score = _score(FakeMouse(), "mouse", {"use_case": "gaming"})
    assert score == 3  # only +3 for weight, no budget bonus


def test_score_switches_any_no_bonus():
    score = _score(FakeKeyboard(), "keyboard", {"use_case": "gaming", "switches": "any", "budget": 5000})
    assert score == 3  # +1 gaming TKL +2 price bonus, no switch bonus
```

- [ ] **Step 3.2: Run to confirm FAIL**

```
cd backend
pytest tests/test_recommendation.py::test_score_gaming_light_mouse_gets_5 -v
```

Expected: `ImportError: cannot import name '_score'`

- [ ] **Step 3.3: Implement engine.py**

Create `backend/app/recommendation/engine.py`:

```python
from sqlalchemy.orm import Session
from app.models.mouse import Mouse
from app.models.keyboard import Keyboard
from app.models.monitor import Monitor

_MODEL_MAP = {
    "mouse": Mouse,
    "keyboard": Keyboard,
    "monitor": Monitor,
}

_SWITCH_KEYWORDS: dict[str, list[str]] = {
    "linear": ["Red", "Silver", "Speed", "Yellow", "Black"],
    "tactile": ["Brown", "Clear", "Tactile"],
    "clicky": ["Blue", "Green", "Clicky"],
}


def recommend(category: str, answers: dict, db: Session) -> list[dict]:
    model = _MODEL_MAP[category]
    query = _build_query(category, answers, db, model)
    products = query.all()

    scored = [(p, _score(p, category, answers)) for p in products]
    scored.sort(key=lambda x: (-x[1], x[0].price or 0))

    return [
        {
            "id": p.id,
            "name": p.name,
            "brand": p.brand,
            "price": p.price,
            "score": score,
            "image_url": p.image_url,
            "dns_url": p.dns_url,
            "wb_url": p.wb_url,
        }
        for p, score in scored[:20]
    ]


def _build_query(category: str, answers: dict, db: Session, model):
    query = db.query(model)

    budget = answers.get("budget")
    if budget is not None:
        query = query.filter(model.price <= float(budget))

    if category == "mouse":
        wireless = answers.get("wireless")
        if wireless == "yes":
            query = query.filter(model.connection_types.contains("Wireless"))
        elif wireless == "no":
            query = query.filter(model.connection_types.contains("USB"))

    elif category == "keyboard":
        form_factor = answers.get("form_factor")
        if form_factor == "full":
            query = query.filter(model.form_factor == "Full")
        elif form_factor == "tkl":
            query = query.filter(model.form_factor == "TKL")
        elif form_factor == "compact":
            query = query.filter(model.form_factor.in_(["60%", "65%", "75%"]))

    elif category == "monitor":
        size = answers.get("size")
        if size == "small":
            query = query.filter(model.diagonal_inch <= 24)
        elif size == "medium":
            query = query.filter(
                model.diagonal_inch >= 24, model.diagonal_inch <= 27
            )
        elif size == "large":
            query = query.filter(model.diagonal_inch >= 27)

    return query


def _score(product, category: str, answers: dict) -> int:
    score = 0
    budget = answers.get("budget")

    if budget is not None and product.price is not None:
        if product.price <= float(budget) * 0.7:
            score += 2

    use_case = answers.get("use_case")

    if category == "mouse":
        if use_case == "gaming" and product.weight_g is not None and product.weight_g <= 80:
            score += 3
        elif use_case == "office" and product.weight_g is not None and product.weight_g >= 90:
            score += 1

    elif category == "keyboard":
        switches_pref = answers.get("switches")
        if switches_pref and switches_pref != "any" and product.switches:
            keywords = _SWITCH_KEYWORDS.get(switches_pref, [])
            if any(kw.lower() in product.switches.lower() for kw in keywords):
                score += 3
        if use_case == "gaming" and product.form_factor in ("TKL", "Full"):
            score += 1

    elif category == "monitor":
        if use_case == "gaming" and product.refresh_rate_hz is not None and product.refresh_rate_hz >= 144:
            score += 3
        elif use_case == "work" and product.matrix_type == "IPS":
            score += 2

    return score
```

- [ ] **Step 3.4: Run to confirm PASS**

```
cd backend
pytest tests/test_recommendation.py -v
```

Expected: 19 passed

- [ ] **Step 3.5: Commit**

```
git add backend/app/recommendation/engine.py backend/tests/test_recommendation.py
git commit -m "feat: add recommendation engine with filter builder and relevance scorer"
```

---

## Task 4: Router + Registration

**Files:**
- Create: `backend/app/routers/recommendation.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_recommendation.py` (append integration tests)

- [ ] **Step 4.1: Append integration tests**

Add to `backend/tests/test_recommendation.py`:

```python
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
```

- [ ] **Step 4.2: Run to confirm FAIL**

```
cd backend
pytest tests/test_recommendation.py::test_questions_endpoint_mouse_returns_3 -v
```

Expected: `404 Not Found` (router not registered yet)

- [ ] **Step 4.3: Create router**

Create `backend/app/routers/recommendation.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.recommendation.questions import get_questions, SUPPORTED_CATEGORIES
from app.recommendation.engine import recommend
from app.schemas.recommendation import (
    RecommendRequest,
    RecommendResponse,
    QuestionsResponse,
)

router = APIRouter(prefix="/recommend", tags=["recommendation"])


@router.get("/questions/{category}", response_model=QuestionsResponse)
def get_category_questions(category: str):
    if category not in SUPPORTED_CATEGORIES:
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")
    return {"category": category, "questions": get_questions(category)}


@router.post("/", response_model=RecommendResponse)
def recommend_products(request: RecommendRequest, db: Session = Depends(get_db)):
    if request.category not in SUPPORTED_CATEGORIES:
        raise HTTPException(status_code=404, detail=f"Category '{request.category}' not found")
    results = recommend(request.category, request.answers, db)
    return {"category": request.category, "total": len(results), "results": results}
```

- [ ] **Step 4.4: Register router in main.py**

Open `backend/app/main.py` and add two lines:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import mice, keyboards, mousepads, monitors, microphones, headphones
from app.routers import recommendation  # добавить

app = FastAPI(title="Peripheral DSS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(mice.router)
app.include_router(keyboards.router)
app.include_router(mousepads.router)
app.include_router(monitors.router)
app.include_router(microphones.router)
app.include_router(headphones.router)
app.include_router(recommendation.router)  # добавить

@app.get("/")
def root():
    return {"message": "Peripheral DSS API"}
```

- [ ] **Step 4.5: Run all tests**

```
cd backend
pytest tests/test_recommendation.py -v
```

Expected: 27 passed, 0 failed

- [ ] **Step 4.6: Run full test suite to check for regressions**

```
cd backend
pytest tests/ -v
```

Expected: все тесты проходят

- [ ] **Step 4.7: Commit**

```
git add backend/app/routers/recommendation.py backend/app/main.py backend/tests/test_recommendation.py
git commit -m "feat: add recommendation router and register endpoints"
```

---

## Task 5: Manual Smoke Test via Swagger

- [ ] **Step 5.1: Start the server**

```
cd backend
uvicorn app.main:app --reload
```

- [ ] **Step 5.2: Open Swagger UI**

Открой в браузере: `http://localhost:8000/docs`

Проверь что в списке эндпоинтов появился раздел **recommendation** с двумя эндпоинтами:
- `GET /recommend/questions/{category}`
- `POST /recommend/`

- [ ] **Step 5.3: Test GET questions**

В Swagger нажми `GET /recommend/questions/{category}` → Try it out → category: `mouse` → Execute.

Ожидаемый ответ:
```json
{
  "category": "mouse",
  "questions": [
    { "id": "use_case", "type": "choice", ... },
    { "id": "wireless", "type": "choice", ... },
    { "id": "budget", "type": "number", ... }
  ]
}
```

- [ ] **Step 5.4: Test POST recommend**

В Swagger нажми `POST /recommend/` → Try it out → вставь тело:
```json
{
  "category": "mouse",
  "answers": {
    "use_case": "gaming",
    "wireless": "no",
    "budget": 5000
  }
}
```

Ожидаемый ответ (пустая БД):
```json
{ "category": "mouse", "total": 0, "results": [] }
```

- [ ] **Step 5.5: Final commit если всё ок**

```
git add .
git status  # убедиться что нет лишних файлов
git commit -m "feat: recommendation engine module complete"
```
