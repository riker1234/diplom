# Wildberries Parser Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fetch mouse products from Wildberries public API and save them to the database via a protected admin endpoint.

**Architecture:** Three layers — `wildberries.py` handles all WB API calls and DB upsert logic, `admin.py` exposes a single protected FastAPI endpoint, `config.py` provides the admin key. Tests mock all network calls so no real internet connection is needed.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, requests, pydantic-settings, pytest + unittest.mock

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `backend/app/config.py` | Add `ADMIN_KEY` setting |
| Modify | `backend/.env` | Add `ADMIN_KEY=diplom2026` |
| Create | `backend/app/parsers/wildberries.py` | WB API client + characteristic mapper + upsert |
| Create | `backend/app/routers/admin.py` | Single protected endpoint |
| Modify | `backend/app/main.py` | Register admin router |
| Create | `backend/tests/test_wildberries_parser.py` | All tests for this module |

---

## Task 1: Add ADMIN_KEY to Config

**Files:**
- Modify: `backend/app/config.py`
- Modify: `backend/.env`
- Test: `backend/tests/test_wildberries_parser.py`

- [ ] **Step 1.1: Write failing test**

Create `backend/tests/test_wildberries_parser.py`:

```python
from app.config import settings


def test_admin_key_is_set():
    assert settings.ADMIN_KEY is not None
    assert len(settings.ADMIN_KEY) > 0
```

- [ ] **Step 1.2: Run to confirm FAIL**

```
cd backend
venv/Scripts/python -m pytest tests/test_wildberries_parser.py -v
```

Expected: `AttributeError: 'Settings' object has no attribute 'ADMIN_KEY'`

- [ ] **Step 1.3: Add ADMIN_KEY to config.py**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/peripheral_dss"
    DNS_UPDATE_INTERVAL_HOURS: int = 12
    WB_UPDATE_INTERVAL_HOURS: int = 12
    ADMIN_KEY: str = "diplom2026"

settings = Settings()
```

- [ ] **Step 1.4: Add ADMIN_KEY to .env**

Append to `backend/.env`:
```
ADMIN_KEY=diplom2026
```

- [ ] **Step 1.5: Run to confirm PASS**

```
cd backend
venv/Scripts/python -m pytest tests/test_wildberries_parser.py -v
```

Expected: `1 passed`

- [ ] **Step 1.6: Commit**

```
cd ..
git add backend/app/config.py backend/.env backend/tests/test_wildberries_parser.py
git commit -m "feat: add ADMIN_KEY to config"
```

---

## Task 2: Characteristic Mapper

**Files:**
- Create: `backend/app/parsers/wildberries.py`
- Modify: `backend/tests/test_wildberries_parser.py`

Это чистые функции без зависимостей — легко тестировать изолированно.

- [ ] **Step 2.1: Append failing tests**

Add to `backend/tests/test_wildberries_parser.py`:

```python
from app.parsers.wildberries import _map_mouse_characteristics, _parse_weight, _build_image_url


def test_parse_weight_grams():
    assert _parse_weight("95 г") == 95.0


def test_parse_weight_with_comma():
    assert _parse_weight("95,5 г") == 95.5


def test_parse_weight_no_number_returns_none():
    assert _parse_weight("нет данных") is None


def test_map_weight_characteristic():
    options = [{"name": "Вес", "value": "70 г"}]
    result = _map_mouse_characteristics(options)
    assert result["weight_g"] == 70.0


def test_map_connection_types():
    options = [{"name": "Тип подключения", "value": "USB"}]
    result = _map_mouse_characteristics(options)
    assert result["connection_types"] == "USB"


def test_map_sensor():
    options = [{"name": "Сенсор", "value": "PixArt 3212"}]
    result = _map_mouse_characteristics(options)
    assert result["sensor"] == "PixArt 3212"


def test_map_switches():
    options = [{"name": "Переключатели", "value": "Omron"}]
    result = _map_mouse_characteristics(options)
    assert result["switches"] == "Omron"


def test_map_unknown_characteristic_returns_none():
    options = [{"name": "Цвет", "value": "Чёрный"}]
    result = _map_mouse_characteristics(options)
    assert result == {"weight_g": None, "connection_types": None, "sensor": None, "switches": None}


def test_map_empty_options_returns_none_fields():
    result = _map_mouse_characteristics([])
    assert result == {"weight_g": None, "connection_types": None, "sensor": None, "switches": None}


def test_build_image_url_contains_product_id():
    url = _build_image_url(12345678)
    assert "12345678" in url
    assert url.startswith("https://basket-")
    assert url.endswith("1.webp")
```

- [ ] **Step 2.2: Run to confirm FAIL**

```
cd backend
venv/Scripts/python -m pytest tests/test_wildberries_parser.py -v
```

Expected: `ImportError: cannot import name '_map_mouse_characteristics'`

- [ ] **Step 2.3: Create wildberries.py with mapper functions**

Create `backend/app/parsers/wildberries.py`:

```python
import re
import requests
from sqlalchemy.orm import Session
from app.models.mouse import Mouse

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

_WEIGHT_KEYS = {"вес", "масса"}
_CONNECTION_KEYS = {"тип подключения", "интерфейс"}
_SENSOR_KEYS = {"сенсор", "тип сенсора"}
_SWITCH_KEYS = {"переключатели", "микровыключатели"}


def _parse_weight(value: str) -> float | None:
    match = re.search(r"[\d]+[.,]?[\d]*", value)
    if match:
        return float(match.group().replace(",", "."))
    return None


def _map_mouse_characteristics(options: list[dict]) -> dict:
    result = {"weight_g": None, "connection_types": None, "sensor": None, "switches": None}
    for opt in options:
        name = opt.get("name", "").lower().strip()
        value = opt.get("value", "").strip()
        if name in _WEIGHT_KEYS:
            result["weight_g"] = _parse_weight(value)
        elif name in _CONNECTION_KEYS:
            result["connection_types"] = value
        elif name in _SENSOR_KEYS:
            result["sensor"] = value
        elif name in _SWITCH_KEYS:
            result["switches"] = value
    return result


def _get_basket(vol: int) -> str:
    thresholds = [
        143, 287, 431, 719, 1007, 1061, 1115, 1169, 1313, 1601,
        1655, 1919, 2045, 2189, 2405, 2621, 2837, 3053, 3269, 3485,
        3701, 3917, 4133, 4349,
    ]
    for i, t in enumerate(thresholds):
        if vol <= t:
            return str(i + 1).zfill(2)
    return "25"


def _build_image_url(product_id: int) -> str:
    vol = product_id // 100000
    part = product_id // 1000
    basket = _get_basket(vol)
    return f"https://basket-{basket}.wbbasket.ru/vol{vol}/part{part}/{product_id}/images/big/1.webp"
```

- [ ] **Step 2.4: Run to confirm PASS**

```
cd backend
venv/Scripts/python -m pytest tests/test_wildberries_parser.py -v
```

Expected: `11 passed`

- [ ] **Step 2.5: Commit**

```
cd ..
git add backend/app/parsers/wildberries.py backend/tests/test_wildberries_parser.py
git commit -m "feat: add WB characteristic mapper and image URL builder"
```

---

## Task 3: WB API Client + Parser Core

**Files:**
- Modify: `backend/app/parsers/wildberries.py`
- Modify: `backend/tests/test_wildberries_parser.py`

- [ ] **Step 3.1: Append tests with mocked API calls**

Add to `backend/tests/test_wildberries_parser.py`:

```python
from unittest.mock import patch, MagicMock
from app.parsers.wildberries import _search_wb, _fetch_details, parse_mice

_FAKE_SEARCH_RESPONSE = {
    "data": {
        "products": [
            {"id": 12345678, "name": "Игровая мышь Test", "brand": "TestBrand", "priceU": 199000},
        ]
    }
}

_FAKE_DETAIL_RESPONSE = {
    "data": {
        "products": [
            {
                "id": 12345678,
                "options": [
                    {"name": "Вес", "value": "70 г"},
                    {"name": "Тип подключения", "value": "USB"},
                ],
            }
        ]
    }
}


def test_search_wb_returns_products():
    with patch("app.parsers.wildberries.requests.get") as mock_get:
        mock_get.return_value.json.return_value = _FAKE_SEARCH_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        result = _search_wb("игровая мышь")
    assert len(result) == 1
    assert result[0]["id"] == 12345678


def test_fetch_details_returns_products():
    with patch("app.parsers.wildberries.requests.get") as mock_get:
        mock_get.return_value.json.return_value = _FAKE_DETAIL_RESPONSE
        mock_get.return_value.raise_for_status = MagicMock()
        result = _fetch_details([12345678])
    assert len(result) == 1
    assert result[0]["id"] == 12345678


def test_parse_mice_adds_new_product(db):
    with patch("app.parsers.wildberries._search_wb", return_value=_FAKE_SEARCH_RESPONSE["data"]["products"]):
        with patch("app.parsers.wildberries._fetch_details", return_value=_FAKE_DETAIL_RESPONSE["data"]["products"]):
            result = parse_mice(db)
    assert result["added"] == 1
    assert result["updated"] == 0
    assert result["failed"] == 0
    mouse = db.query(Mouse).filter(Mouse.wb_sku == "12345678").first()
    assert mouse is not None
    assert mouse.weight_g == 70.0
    assert mouse.price == 1990.0


def test_parse_mice_updates_existing_product(db):
    existing = Mouse(name="Old Name", price=1000.0, wb_sku="99999999")
    db.add(existing)
    db.commit()
    updated_search = [{"id": 99999999, "name": "New Name", "brand": "Brand", "priceU": 250000}]
    with patch("app.parsers.wildberries._search_wb", return_value=updated_search):
        with patch("app.parsers.wildberries._fetch_details", return_value=[]):
            result = parse_mice(db)
    assert result["updated"] == 1
    assert result["added"] == 0
    mouse = db.query(Mouse).filter(Mouse.wb_sku == "99999999").first()
    assert mouse.price == 2500.0
```

- [ ] **Step 3.2: Run to confirm FAIL**

```
cd backend
venv/Scripts/python -m pytest tests/test_wildberries_parser.py::test_search_wb_returns_products -v
```

Expected: `ImportError: cannot import name '_search_wb'`

- [ ] **Step 3.3: Add API client and parse_mice to wildberries.py**

Append to `backend/app/parsers/wildberries.py`:

```python
def _search_wb(query: str, limit: int = 100) -> list[dict]:
    url = "https://search.wb.ru/exactmatch/ru/common/v5/search"
    params = {"query": query, "resultset": "catalog", "limit": limit, "dest": "-1257786"}
    resp = requests.get(url, params=params, headers=_HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json().get("data", {}).get("products", [])


def _fetch_details(product_ids: list[int]) -> list[dict]:
    url = "https://card.wb.ru/cards/v1/detail"
    params = {
        "appType": "1",
        "curr": "rub",
        "dest": "-1257786",
        "nm": ";".join(str(i) for i in product_ids),
    }
    resp = requests.get(url, params=params, headers=_HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json().get("data", {}).get("products", [])


def parse_mice(db: Session) -> dict:
    added = updated = failed = 0

    products = _search_wb("игровая мышь")
    if not products:
        return {"added": 0, "updated": 0, "failed": 0}

    product_ids = [p["id"] for p in products]
    details = _fetch_details(product_ids)
    details_map = {d["id"]: d for d in details}

    for product in products:
        try:
            pid = product["id"]
            options = details_map.get(pid, {}).get("options", [])
            chars = _map_mouse_characteristics(options)

            wb_sku = str(pid)
            price = product.get("priceU", 0) / 100

            existing = db.query(Mouse).filter(Mouse.wb_sku == wb_sku).first()
            if existing:
                existing.price = price
                existing.image_url = _build_image_url(pid)
                db.commit()
                updated += 1
            else:
                db.add(Mouse(
                    name=product.get("name", ""),
                    brand=product.get("brand", ""),
                    price=price,
                    wb_sku=wb_sku,
                    wb_url=f"https://www.wildberries.ru/catalog/{pid}/detail.aspx",
                    image_url=_build_image_url(pid),
                    **chars,
                ))
                db.commit()
                added += 1
        except Exception:
            failed += 1
            db.rollback()

    return {"added": added, "updated": updated, "failed": failed}
```

- [ ] **Step 3.4: Run to confirm PASS**

```
cd backend
venv/Scripts/python -m pytest tests/test_wildberries_parser.py -v
```

Expected: `16 passed`

- [ ] **Step 3.5: Commit**

```
cd c:/Users/User/Desktop/diplom
git add backend/app/parsers/wildberries.py backend/tests/test_wildberries_parser.py
git commit -m "feat: add WB API client and parse_mice function"
```

---

## Task 4: Admin Router + Registration

**Files:**
- Create: `backend/app/routers/admin.py`
- Modify: `backend/app/main.py`
- Modify: `backend/tests/test_wildberries_parser.py`

- [ ] **Step 4.1: Append endpoint tests**

Add to `backend/tests/test_wildberries_parser.py`:

```python
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

_TEST_DB_URL = "sqlite:///./test_parser.db"
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


def test_parse_endpoint_without_key_returns_422():
    resp = _client.post("/admin/parse/wildberries/mouse")
    assert resp.status_code == 422


def test_parse_endpoint_wrong_key_returns_403():
    resp = _client.post(
        "/admin/parse/wildberries/mouse",
        headers={"X-Admin-Key": "wrong-key"},
    )
    assert resp.status_code == 403


def test_parse_endpoint_correct_key_returns_200():
    with patch("app.routers.admin.parse_mice", return_value={"added": 5, "updated": 0, "failed": 0}):
        resp = _client.post(
            "/admin/parse/wildberries/mouse",
            headers={"X-Admin-Key": "diplom2026"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["added"] == 5
    assert "updated" in data
    assert "failed" in data
```

- [ ] **Step 4.2: Run to confirm FAIL**

```
cd backend
venv/Scripts/python -m pytest tests/test_wildberries_parser.py::test_parse_endpoint_without_key_returns_422 -v
```

Expected: `404 Not Found` (endpoint doesn't exist yet)

- [ ] **Step 4.3: Create admin router**

Create `backend/app/routers/admin.py`:

```python
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.parsers.wildberries import parse_mice

router = APIRouter(prefix="/admin", tags=["admin"])


def _verify_admin_key(x_admin_key: str = Header(...)):
    if x_admin_key != settings.ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")


@router.post("/parse/wildberries/mouse")
def parse_wildberries_mouse(
    db: Session = Depends(get_db),
    _: None = Depends(_verify_admin_key),
):
    return parse_mice(db)
```

- [ ] **Step 4.4: Register admin router in main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import mice, keyboards, mousepads, monitors, microphones, headphones
from app.routers import recommendation
from app.routers import admin  # добавить

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
app.include_router(recommendation.router)
app.include_router(admin.router)  # добавить

@app.get("/")
def root():
    return {"message": "Peripheral DSS API"}
```

- [ ] **Step 4.5: Run all tests**

```
cd backend
venv/Scripts/python -m pytest tests/test_wildberries_parser.py -v
```

Expected: `19 passed`

- [ ] **Step 4.6: Run full test suite to check for regressions**

```
cd backend
venv/Scripts/python -m pytest tests/ -v
```

Expected: все тесты проходят

- [ ] **Step 4.7: Commit**

```
cd ..
git add backend/app/routers/admin.py backend/app/main.py backend/tests/test_wildberries_parser.py
git commit -m "feat: add admin router with WB mouse parser endpoint"
```

---

## Task 5: Manual Smoke Test

- [ ] **Step 5.1: Start server (Docker должен быть запущен)**

```
cd backend
venv/Scripts/uvicorn app.main:app --reload
```

- [ ] **Step 5.2: Открой Swagger**

`http://localhost:8000/docs` — проверь что появился раздел **admin** с эндпоинтом `POST /admin/parse/wildberries/mouse`

- [ ] **Step 5.3: Запусти парсер**

В Swagger: `POST /admin/parse/wildberries/mouse` → Try it out → добавь заголовок:
```
X-Admin-Key: diplom2026
```
→ Execute

Ожидаемый ответ (займёт 5–15 секунд):
```json
{"added": 80, "updated": 0, "failed": 5}
```

- [ ] **Step 5.4: Проверь что товары появились в БД**

В Swagger: `GET /mice/` → Execute

Ожидаемый результат: список мышей с названиями, ценами и характеристиками.

- [ ] **Step 5.5: Проверь движок рекомендаций с реальными данными**

В Swagger: `POST /recommend/` → Try it out:
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

Ожидаемый результат: список мышей с ненулевым `total` и баллами `score`.
