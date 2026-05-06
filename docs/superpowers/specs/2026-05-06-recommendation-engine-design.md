# Recommendation Engine — Design Spec

**Date:** 2026-05-06  
**Module:** `app/recommendation/`  
**Status:** Approved, ready for implementation

---

## Context

The recommendation engine is the core of the DSS. It takes a user's questionnaire answers and returns a filtered, relevance-scored list of peripheral products from the database.

Existing codebase already has: SQLAlchemy models for 6 categories, FastAPI CRUD routers with filtering, Pydantic schemas, PostgreSQL via Docker.

---

## Scope

**In scope:** Mouse, Keyboard, Monitor (3 categories for MVP)  
**Out of scope:** Headphones, Microphone, Mousepad (added later by extending `questions.py`)

---

## Architecture

Three new files + registration in `main.py`:

```
app/
├── recommendation/
│   ├── __init__.py        (exists, empty)
│   ├── questions.py       ← questionnaire definitions for 3 categories
│   └── engine.py          ← filter builder + relevance scorer
└── routers/
    └── recommendation.py  ← 2 new endpoints
```

Data flow:
```
GET /recommend/questions/{category}
    → questions.py returns question structure for frontend wizard

POST /recommend/ {category, answers}
    → engine.py builds hard filters from answers
    → engine.py queries DB via SQLAlchemy
    → engine.py scores each result
    → router returns list sorted by score DESC, price ASC
```

---

## Questionnaires

### Mouse (3 questions)

| id | text | type | options |
|---|---|---|---|
| `use_case` | «Для чего используете мышь?» | choice | gaming / office / both |
| `wireless` | «Нужна беспроводная?» | choice | yes / no / any |
| `budget` | «Максимальный бюджет (₽)?» | number | free input |

### Keyboard (4 questions)

| id | text | type | options |
|---|---|---|---|
| `use_case` | «Для чего используете клавиатуру?» | choice | gaming / typing / both |
| `form_factor` | «Форм-фактор?» | choice | full / tkl / compact |
| `switches` | «Тип переключателей?» | choice | linear / tactile / clicky / any |
| `budget` | «Максимальный бюджет (₽)?» | number | free input |

### Monitor (3 questions)

| id | text | type | options |
|---|---|---|---|
| `use_case` | «Основное использование?» | choice | gaming / work / both |
| `size` | «Размер экрана?» | choice | small / medium / large / any |
| `budget` | «Максимальный бюджет (₽)?» | number | free input |

---

## Filter & Scoring Logic

### Hard filters (exclude products that don't match)

| Category | Answer | SQL filter |
|---|---|---|
| All | `budget = N` | `price <= N` |
| Mouse | `wireless = yes` | `connection_types LIKE '%Wireless%'` |
| Mouse | `wireless = no` | `connection_types LIKE '%USB%'` |
| Mouse | `wireless = any` | no filter applied |
| Keyboard | `form_factor = full` | `form_factor = 'Full'` |
| Keyboard | `form_factor = tkl` | `form_factor = 'TKL'` |
| Keyboard | `form_factor = compact` | `form_factor IN ('60%','65%','75%')` — exact values must match what's stored in DB |
| Monitor | `size = small` | `diagonal_inch <= 24` |
| Monitor | `size = medium` | `diagonal_inch BETWEEN 24 AND 27` |
| Monitor | `size = large` | `diagonal_inch >= 27` |
| Monitor | `size = any` | no filter applied |

### Soft scoring (add points to relevance score)

| Condition | Points |
|---|---|
| `price <= budget * 0.7` | +2 |
| Mouse: `use_case=gaming` AND `weight_g <= 80` | +3 |
| Mouse: `use_case=office` AND `weight_g >= 90` | +1 |
| Monitor: `use_case=gaming` AND `refresh_rate_hz >= 144` | +3 |
| Monitor: `use_case=work` AND `matrix_type = 'IPS'` | +2 |
| Keyboard: switches answer matches product switches | +3 |
| Keyboard: `use_case=gaming` AND `form_factor IN (TKL, Full)` | +1 |

Switch matching rules:
- `linear` → switches contains «Red», «Silver», «Speed», «Yellow»
- `tactile` → switches contains «Brown», «Clear», «Tactile»
- `clicky` → switches contains «Blue», «Green», «Clicky»

### Result sorting

`ORDER BY score DESC, price ASC LIMIT 20`

### Empty results

If no products match hard filters: return `{"total": 0, "results": []}` with HTTP 200.  
No filter relaxation in MVP.

---

## API Endpoints

### GET `/recommend/questions/{category}`

Returns the questionnaire structure for the given category.

**Path params:** `category` ∈ `{mouse, keyboard, monitor}`

**Response 200:**
```json
{
  "category": "mouse",
  "questions": [
    {
      "id": "use_case",
      "text": "Для чего используете мышь?",
      "type": "choice",
      "options": [
        {"value": "gaming", "label": "Для игр"},
        {"value": "office", "label": "Для работы"},
        {"value": "both",   "label": "Для всего"}
      ]
    },
    {
      "id": "wireless",
      "text": "Нужна беспроводная?",
      "type": "choice",
      "options": [
        {"value": "yes", "label": "Да"},
        {"value": "no",  "label": "Нет, проводная"},
        {"value": "any", "label": "Не важно"}
      ]
    },
    {
      "id": "budget",
      "text": "Максимальный бюджет (₽)?",
      "type": "number",
      "placeholder": "Например: 3000"
    }
  ]
}
```

**Response 404:** category not found.

---

### POST `/recommend/`

Accepts questionnaire answers, returns scored product list.

**Request body:**
```json
{
  "category": "mouse",
  "answers": {
    "use_case": "gaming",
    "wireless": "no",
    "budget": 3000
  }
}
```

**Response 200:**
```json
{
  "category": "mouse",
  "total": 5,
  "results": [
    {
      "id": 1,
      "name": "Razer Viper Mini",
      "brand": "Razer",
      "price": 2100.0,
      "score": 5,
      "image_url": "https://...",
      "dns_url": "https://...",
      "wb_url": "https://..."
    }
  ]
}
```

**Response 422:** invalid category or answer values (Pydantic validation).

---

## Pydantic Schemas

```python
# RecommendRequest
category: str          # "mouse" | "keyboard" | "monitor"
answers: dict[str, str | int | float]

# RecommendResultItem
id: int
name: str
brand: Optional[str]
price: Optional[float]
score: int
image_url: Optional[str]
dns_url: Optional[str]
wb_url: Optional[str]

# RecommendResponse
category: str
total: int
results: list[RecommendResultItem]
```

---

## `questions.py` Structure

```python
QUESTIONS: dict[str, list[dict]] = {
    "mouse": [...],
    "keyboard": [...],
    "monitor": [...],
}

def get_questions(category: str) -> list[dict]:
    if category not in QUESTIONS:
        return None
    return QUESTIONS[category]
```

---

## `engine.py` Structure

```python
def recommend(category: str, answers: dict, db: Session) -> list[dict]:
    # 1. Build hard filters → SQLAlchemy query
    # 2. Execute query → list of ORM objects
    # 3. Score each object
    # 4. Sort by score DESC, price ASC
    # 5. Return list of dicts (max 20)

def _build_query(category: str, answers: dict, db: Session):
    # Returns filtered SQLAlchemy query

def _score(product, category: str, answers: dict) -> int:
    # Returns relevance score for a single product
```

---

## Registration in main.py

```python
from app.routers import recommendation
app.include_router(recommendation.router)
```

---

## Testing

- `GET /recommend/questions/mouse` → returns 3 questions
- `GET /recommend/questions/invalid` → 404
- `POST /recommend/` with valid mouse answers → 200, results list
- `POST /recommend/` with budget=1 (nothing matches) → 200, empty results
- `POST /recommend/` with unknown category → 422
- Score ordering: cheaper gaming mouse with weight ≤ 80g ranks above heavier one
