# Ozon Parser Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace Wildberries parser with Ozon parser across all 6 peripheral categories, removing all WB/DNS-specific model fields.

**Architecture:** New `ozon.py` mirrors `wildberries.py` structure — helpers, key maps, mappers, search, details, upsert loop. Ozon data comes from `requests` to the internal `entrypoint-api.bx` JSON API. Models swap `wb_sku`/`wb_url`/`dns_*` for `ozon_sku`/`ozon_url` via Alembic migration.

**Tech Stack:** Python requests, SQLAlchemy, Alembic, FastAPI, pytest, SQLite (tests), PostgreSQL (prod)

---

## File Map

| File | Change |
|------|--------|
| `backend/app/models/mouse.py` | Remove wb_sku, wb_url, dns_*; add ozon_sku, ozon_url |
| `backend/app/models/keyboard.py` | Same |
| `backend/app/models/monitor.py` | Same |
| `backend/app/models/headphones.py` | Same |
| `backend/app/models/microphone.py` | Same |
| `backend/app/models/mousepad.py` | Same |
| `backend/alembic/versions/XXXX_ozon_fields.py` | New migration |
| `backend/app/parsers/ozon.py` | Create |
| `backend/app/parsers/wildberries.py` | Delete |
| `backend/app/routers/admin.py` | Swap WB → Ozon imports |
| `backend/tests/test_ozon_parser.py` | Create |
| `backend/tests/test_wildberries_parser.py` | Delete |

---

## Task 1: Probe Ozon API

**Goal:** Discover the real JSON structure and Russian characteristic field names before writing any production code.

**Files:**
- Create: `backend/test_ozon_probe.py`

- [ ] **Step 1: Write probe script**

```python
# backend/test_ozon_probe.py
import sys, json, requests
sys.stdout.reconfigure(encoding='utf-8')
from urllib.parse import quote

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "x-o3-app-name": "ozonweb",
    "x-o3-app-version": "5.0.0",
    "Accept": "application/json",
    "Accept-Language": "ru-RU,ru;q=0.9",
}

BASE = "https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2"

# ── 1. Search ────────────────────────────────────────────────
print("=== SEARCH ===")
resp = requests.get(
    BASE,
    params={"url": "/search/?text=игровая+мышь&layout_container=categorySearchMegapagination&layout_page_index=1"},
    headers=HEADERS,
    timeout=30,
)
print(f"Status: {resp.status_code}")

if resp.status_code == 200:
    data = resp.json()
    print(f"Top-level keys: {list(data.keys())}")
    widget_states = data.get("widgetStates", {})
    print(f"widgetStates count: {len(widget_states)}")

    # Find product list widget
    for key in widget_states:
        if any(x in key for x in ["searchResultsV2", "tileGrid", "searchResults"]):
            print(f"\nFound widget key: {key}")
            try:
                w = json.loads(widget_states[key])
                items = w.get("items", [])
                print(f"Items count: {len(items)}")
                if items:
                    print("\nFirst item keys:", list(items[0].keys()))
                    print("First item sample:")
                    print(json.dumps(items[0], ensure_ascii=False, indent=2)[:2000])
            except Exception as e:
                print(f"Parse error: {e}")
            break

# ── 2. Product characteristics ──────────────────────────────
# Replace 123456789 with a real Ozon product ID from search above
TEST_ID = 123456789
print(f"\n=== PRODUCT CHARS (id={TEST_ID}) ===")
resp2 = requests.get(
    BASE,
    params={"url": f"/product/{TEST_ID}/"},
    headers=HEADERS,
    timeout=30,
)
print(f"Status: {resp2.status_code}")
if resp2.status_code == 200:
    data2 = resp2.json()
    widget_states2 = data2.get("widgetStates", {})
    for key in widget_states2:
        if any(x in key for x in ["webCharacteristics", "webDetailSKU", "characteristics"]):
            print(f"\nFound widget key: {key}")
            try:
                w = json.loads(widget_states2[key])
                print(json.dumps(w, ensure_ascii=False, indent=2)[:3000])
            except Exception as e:
                print(f"Parse error: {e}")
```

- [ ] **Step 2: Run the probe**

```
cd backend
.\venv\Scripts\python.exe test_ozon_probe.py
```

Expected: status 200, list of items, first item structure printed.

- [ ] **Step 3: Find a real product ID from the search output, update TEST_ID, re-run to see characteristics**

Look at the `First item sample` output. Find the field that holds product ID (likely `"id"`, `"sku"`, or inside `"action"."link"`). Update `TEST_ID` in the script and re-run.

- [ ] **Step 4: Record key findings**

Note down from output:
- Field name for product ID in search items (e.g. `"id"`)
- Field name for product name (e.g. `"name"`)
- Field name for price (may be nested)
- Field name for image URL
- Widget key pattern that contains characteristics
- Structure of characteristics: list of `{"name": ..., "values": [{"text": ...}]}` or similar
- Actual Russian field names for sensor, connection type, weight

These go into Task 5 (key mappings).

---

## Task 2: Update All 6 Models

**Files:**
- Modify: `backend/app/models/mouse.py`
- Modify: `backend/app/models/keyboard.py`
- Modify: `backend/app/models/monitor.py`
- Modify: `backend/app/models/headphones.py`
- Modify: `backend/app/models/microphone.py`
- Modify: `backend/app/models/mousepad.py`

- [ ] **Step 1: Update mouse.py**

```python
# backend/app/models/mouse.py
from sqlalchemy import Column, Integer, String, Float
from app.database import Base
from app.models import TimestampMixin

class Mouse(Base, TimestampMixin):
    __tablename__ = "mice"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String)
    sensor = Column(String)
    switches = Column(String)
    weight_g = Column(Float)
    connection_types = Column(String)
    price = Column(Float)
    ozon_sku = Column(String, unique=True, nullable=True)
    ozon_url = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
```

- [ ] **Step 2: Update keyboard.py**

```python
# backend/app/models/keyboard.py
from sqlalchemy import Column, Integer, String, Float
from app.database import Base
from app.models import TimestampMixin

class Keyboard(Base, TimestampMixin):
    __tablename__ = "keyboards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String)
    switches = Column(String)
    board_material = Column(String)
    form_factor = Column(String)
    keycap_material = Column(String)
    keycap_manufacturing = Column(String)
    connection_types = Column(String)
    price = Column(Float)
    ozon_sku = Column(String, unique=True, nullable=True)
    ozon_url = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
```

- [ ] **Step 3: Update monitor.py**

```python
# backend/app/models/monitor.py
from sqlalchemy import Column, Integer, String, Float, Integer as Int
from app.database import Base
from app.models import TimestampMixin

class Monitor(Base, TimestampMixin):
    __tablename__ = "monitors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String)
    diagonal_inch = Column(Float)
    resolution = Column(String)
    refresh_rate_hz = Column(Integer)
    matrix_type = Column(String)
    price = Column(Float)
    ozon_sku = Column(String, unique=True, nullable=True)
    ozon_url = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
```

- [ ] **Step 4: Update headphones.py**

```python
# backend/app/models/headphones.py
from sqlalchemy import Column, Integer, String, Float, Boolean
from app.database import Base
from app.models import TimestampMixin

class Headphones(Base, TimestampMixin):
    __tablename__ = "headphones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String)
    construction_type = Column(String)
    connection_types = Column(String)
    has_microphone = Column(Boolean, default=False)
    noise_cancellation = Column(String)
    price = Column(Float)
    ozon_sku = Column(String, unique=True, nullable=True)
    ozon_url = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
```

- [ ] **Step 5: Update microphone.py**

```python
# backend/app/models/microphone.py
from sqlalchemy import Column, Integer, String, Float
from app.database import Base
from app.models import TimestampMixin

class Microphone(Base, TimestampMixin):
    __tablename__ = "microphones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String)
    mic_type = Column(String)
    directionality = Column(String)
    connection_types = Column(String)
    frequency_range = Column(String)
    price = Column(Float)
    ozon_sku = Column(String, unique=True, nullable=True)
    ozon_url = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
```

- [ ] **Step 6: Update mousepad.py**

```python
# backend/app/models/mousepad.py
from sqlalchemy import Column, Integer, String, Float, Boolean
from app.database import Base
from app.models import TimestampMixin

class Mousepad(Base, TimestampMixin):
    __tablename__ = "mousepads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String)
    size = Column(String)
    surface_material = Column(String)
    hardness = Column(String)
    has_rgb = Column(Boolean, default=False)
    price = Column(Float)
    ozon_sku = Column(String, unique=True, nullable=True)
    ozon_url = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
```

- [ ] **Step 7: Commit models**

```
git add backend/app/models/
git commit -m "refactor: replace wb/dns fields with ozon_sku/ozon_url in all models"
```

---

## Task 3: Alembic Migration

**Files:**
- Create: `backend/alembic/versions/XXXX_ozon_fields.py` (auto-generated name)

- [ ] **Step 1: Generate migration**

```
cd backend
.\venv\Scripts\alembic.exe revision --autogenerate -m "replace wb dns fields with ozon fields"
```

Expected: new file created in `alembic/versions/`.

- [ ] **Step 2: Open the generated file and verify it contains**

- `op.drop_column` for: `wb_sku`, `wb_url`, `dns_product_id`, `dns_url` on all 6 tables
- `op.add_column` for: `ozon_sku`, `ozon_url` on all 6 tables

If autogenerate missed anything, add manually.

- [ ] **Step 3: Truncate existing data before migration**

Add truncation at the top of `upgrade()` in the generated file:

```python
def upgrade() -> None:
    # Clear stale WB data — all rows will be repopulated from Ozon
    for table in ("mice", "keyboards", "monitors", "headphones", "microphones", "mousepads"):
        op.execute(f"DELETE FROM {table}")
    # ... rest of autogenerated ops
```

- [ ] **Step 4: Apply migration**

```
cd backend
.\venv\Scripts\alembic.exe upgrade head
```

Expected: `Running upgrade ... -> XXXX, replace wb dns fields with ozon fields`

- [ ] **Step 5: Verify in psql**

```
docker compose exec db psql -U postgres peripheral_dss -c "\d mice"
```

Expected: columns `ozon_sku`, `ozon_url` present; `wb_sku`, `wb_url`, `dns_product_id`, `dns_url` absent.

- [ ] **Step 6: Commit migration**

```
git add backend/alembic/versions/
git commit -m "feat: alembic migration — ozon fields, truncate stale WB data"
```

---

## Task 4: Write Failing Tests for ozon.py

**Files:**
- Create: `backend/tests/test_ozon_parser.py`

Use the characteristic field names discovered in Task 1. The examples below use the most likely Ozon field names — adjust to match actual probe output.

- [ ] **Step 1: Create test file**

```python
# backend/tests/test_ozon_parser.py
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from unittest.mock import patch, MagicMock
from app.config import settings
from app.parsers.ozon import (
    _parse_float,
    _parse_int,
    _parse_bool,
    _map_mouse,
    _map_keyboard,
    _map_monitor,
    _map_headphones,
    _map_microphone,
    _map_mousepad,
    _extract_products,
    _fetch_details,
    parse_mice,
)
from app.models.mouse import Mouse


# ── Config ────────────────────────────────────────────────────────────────────

def test_admin_key_is_set():
    assert settings.ADMIN_KEY is not None
    assert len(settings.ADMIN_KEY) > 0


# ── Вспомогательные парсеры значений ──────────────────────────────────────────

def test_parse_float_grams():
    assert _parse_float("95 г") == 95.0

def test_parse_float_with_comma():
    assert _parse_float("95,5 г") == 95.5

def test_parse_float_no_number_returns_none():
    assert _parse_float("нет данных") is None

def test_parse_int_hz():
    assert _parse_int("144 Гц") == 144

def test_parse_int_no_number_returns_none():
    assert _parse_int("нет данных") is None

def test_parse_bool_da():
    assert _parse_bool("Да") is True

def test_parse_bool_net():
    assert _parse_bool("Нет") is False

def test_parse_bool_est():
    assert _parse_bool("Есть") is True


# ── Маппер мыши ───────────────────────────────────────────────────────────────

# Options are flat dicts {"name": ..., "value": ...} — same contract as WB mapper

def test_map_mouse_weight():
    result = _map_mouse([{"name": "Вес", "value": "70 г"}])
    assert result["weight_g"] == 70.0

def test_map_mouse_connection():
    result = _map_mouse([{"name": "Тип подключения", "value": "USB"}])
    assert result["connection_types"] == "USB"

def test_map_mouse_sensor():
    result = _map_mouse([{"name": "Тип сенсора", "value": "PixArt 3395"}])
    assert result["sensor"] == "PixArt 3395"

def test_map_mouse_switches():
    result = _map_mouse([{"name": "Тип переключателей", "value": "Omron"}])
    assert result["switches"] == "Omron"

def test_map_mouse_unknown_field_returns_none():
    result = _map_mouse([{"name": "Цвет", "value": "Чёрный"}])
    assert result == {"weight_g": None, "connection_types": None, "sensor": None, "switches": None}

def test_map_mouse_empty():
    result = _map_mouse([])
    assert result == {"weight_g": None, "connection_types": None, "sensor": None, "switches": None}


# ── Маппер клавиатуры ─────────────────────────────────────────────────────────

def test_map_keyboard_switches():
    result = _map_keyboard([{"name": "Тип переключателей", "value": "Cherry MX Red"}])
    assert result["switches"] == "Cherry MX Red"

def test_map_keyboard_form_factor():
    result = _map_keyboard([{"name": "Форм-фактор", "value": "TKL"}])
    assert result["form_factor"] == "TKL"

def test_map_keyboard_empty():
    result = _map_keyboard([])
    assert all(v is None for v in result.values())


# ── Маппер монитора ───────────────────────────────────────────────────────────

def test_map_monitor_refresh_rate():
    result = _map_monitor([{"name": "Частота обновления экрана", "value": "144 Гц"}])
    assert result["refresh_rate_hz"] == 144

def test_map_monitor_diagonal():
    result = _map_monitor([{"name": "Диагональ экрана", "value": "27\""}])
    assert result["diagonal_inch"] == 27.0

def test_map_monitor_matrix():
    result = _map_monitor([{"name": "Тип матрицы", "value": "IPS"}])
    assert result["matrix_type"] == "IPS"

def test_map_monitor_resolution():
    result = _map_monitor([{"name": "Разрешение экрана", "value": "1920x1080"}])
    assert result["resolution"] == "1920x1080"


# ── Маппер наушников ──────────────────────────────────────────────────────────

def test_map_headphones_has_microphone_yes():
    result = _map_headphones([{"name": "Наличие микрофона", "value": "Да"}])
    assert result["has_microphone"] is True

def test_map_headphones_has_microphone_no():
    result = _map_headphones([{"name": "Наличие микрофона", "value": "Нет"}])
    assert result["has_microphone"] is False

def test_map_headphones_no_mic_defaults_false():
    result = _map_headphones([])
    assert result["has_microphone"] is False


# ── Маппер микрофона ──────────────────────────────────────────────────────────

def test_map_microphone_type():
    result = _map_microphone([{"name": "Тип микрофона", "value": "конденсаторный"}])
    assert result["mic_type"] == "конденсаторный"

def test_map_microphone_connection():
    result = _map_microphone([{"name": "Тип подключения", "value": "USB"}])
    assert result["connection_types"] == "USB"


# ── Маппер коврика ────────────────────────────────────────────────────────────

def test_map_mousepad_has_rgb_yes():
    result = _map_mousepad([{"name": "Подсветка", "value": "Да"}])
    assert result["has_rgb"] is True

def test_map_mousepad_hardness():
    result = _map_mousepad([{"name": "Жёсткость", "value": "мягкий"}])
    assert result["hardness"] == "мягкий"

def test_map_mousepad_no_rgb_defaults_false():
    result = _map_mousepad([])
    assert result["has_rgb"] is False


# ── _extract_products ────────────────────────────────────────────────────────

_FAKE_WIDGET_STATES = {
    "searchResultsV2-123": '{"items": [{"id": 12345678, "name": "Игровая мышь Test", "brand": "TestBrand", "finalPrice": "1990", "images": ["https://cdn.ozon.ru/test.jpg"], "urlForProduct": "/product/test-12345678/"}]}'
}

def test_extract_products_returns_list():
    products = _extract_products(_FAKE_WIDGET_STATES)
    assert len(products) == 1
    assert products[0]["id"] == 12345678

def test_extract_products_empty_widget_states():
    assert _extract_products({}) == []


# ── _fetch_details ────────────────────────────────────────────────────────────

_FAKE_CHARS_WIDGET = {
    "webCharacteristics-456": '{"characteristics": [{"short_characteristics": [{"name": "Тип сенсора", "values": [{"text": "PixArt 3395"}]}, {"name": "Тип подключения", "values": [{"text": "USB"}]}]}]}'
}

def test_fetch_details_parses_characteristics():
    with patch("app.parsers.ozon.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"widgetStates": _FAKE_CHARS_WIDGET}
        result = _fetch_details([12345678], {12345678: "/product/test-12345678/"})
    assert 12345678 in result
    assert isinstance(result[12345678], list)
    assert len(result[12345678]) == 2

def test_fetch_details_empty_on_http_error():
    with patch("app.parsers.ozon.requests.get") as mock_get:
        mock_get.return_value.status_code = 429
        result = _fetch_details([12345678], {12345678: "/product/test-12345678/"})
    assert result == {}


# ── parse_mice (интеграция с БД) ──────────────────────────────────────────────

_FAKE_PRODUCTS = [
    {"id": 12345678, "name": "Игровая мышь Test", "brand": "TestBrand",
     "finalPrice": "1990", "images": ["https://cdn.ozon.ru/test.jpg"],
     "urlForProduct": "/product/test-12345678/"}
]

_FAKE_DETAILS = {
    12345678: [
        {"name": "Тип сенсора", "value": "PixArt 3395"},
        {"name": "Тип подключения", "value": "USB"},
        {"name": "Вес", "value": "70 г"},
    ]
}


def test_parse_mice_adds_new_product(db):
    with patch("app.parsers.ozon._fetch_all", return_value=(_FAKE_PRODUCTS, _FAKE_DETAILS)):
        result = parse_mice(db)
    assert result["added"] == 1
    assert result["updated"] == 0
    assert result["failed"] == 0
    mouse = db.query(Mouse).filter(Mouse.ozon_sku == "12345678").first()
    assert mouse is not None
    assert mouse.weight_g == 70.0
    assert mouse.connection_types == "USB"
    assert mouse.price == 1990.0


def test_parse_mice_updates_existing(db):
    existing = Mouse(name="Old", price=500.0, ozon_sku="99999999")
    db.add(existing)
    db.commit()
    updated_products = [
        {"id": 99999999, "name": "New", "brand": "B", "finalPrice": "2500",
         "images": [], "urlForProduct": "/product/new-99999999/"}
    ]
    with patch("app.parsers.ozon._fetch_all", return_value=(updated_products, {})):
        result = parse_mice(db)
    assert result["updated"] == 1
    mouse = db.query(Mouse).filter(Mouse.ozon_sku == "99999999").first()
    assert mouse.price == 2500.0


def test_parse_mice_returns_error_on_exception(db):
    with patch("app.parsers.ozon._fetch_all", side_effect=RuntimeError("timeout")):
        result = parse_mice(db)
    assert "error" in result
    assert result["added"] == 0
```

- [ ] **Step 2: Run tests to confirm they fail (ozon.py doesn't exist yet)**

```
cd backend
.\venv\Scripts\python.exe -m pytest tests/test_ozon_parser.py -x -q 2>&1 | Select-Object -First 20
```

Expected: `ImportError: cannot import name '_parse_float' from 'app.parsers.ozon'`

---

## Task 5: Implement ozon.py

**Files:**
- Create: `backend/app/parsers/ozon.py`

**Note:** Fill in the actual Russian field names in `_MOUSE_KEYS` etc. based on what you found in Task 1 Step 4. The keys below are starting points — you will likely need to adjust them after checking real Ozon characteristics output.

- [ ] **Step 1: Create ozon.py**

```python
# backend/app/parsers/ozon.py
import re
import json
import time
import random
import requests
from urllib.parse import quote
from sqlalchemy.orm import Session
from app.models.mouse import Mouse
from app.models.keyboard import Keyboard
from app.models.monitor import Monitor
from app.models.headphones import Headphones
from app.models.microphone import Microphone
from app.models.mousepad import Mousepad

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "x-o3-app-name": "ozonweb",
    "x-o3-app-version": "5.0.0",
    "Accept": "application/json",
    "Accept-Language": "ru-RU,ru;q=0.9",
}

_BASE_URL = "https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2"

# ── Ключи характеристик Ozon (русские названия полей) ─────────────────────────
# IMPORTANT: Verify these against actual Ozon output from test_ozon_probe.py
# and update to match real field names.

_MOUSE_KEYS = {
    "weight":           {"вес", "вес товара", "вес с упаковкой"},
    "connection_types": {"тип подключения", "интерфейс подключения", "интерфейс"},
    "sensor":           {"тип сенсора", "сенсор", "тип датчика"},
    "switches":         {"тип переключателей", "переключатели", "микровыключатели"},
}

_KEYBOARD_KEYS = {
    "switches":             {"тип переключателей", "переключатели", "тип свитчей"},
    "form_factor":          {"форм-фактор", "размер клавиатуры", "конструкция"},
    "board_material":       {"материал корпуса"},
    "keycap_material":      {"материал клавиш", "материал кейкапов"},
    "keycap_manufacturing": {"способ нанесения символов", "нанесение символов"},
    "connection_types":     {"тип подключения", "интерфейс"},
}

_MONITOR_KEYS = {
    "diagonal_inch":   {"диагональ экрана", "диагональ", "размер экрана"},
    "resolution":      {"разрешение экрана", "разрешение"},
    "refresh_rate_hz": {"частота обновления экрана", "частота обновления"},
    "matrix_type":     {"тип матрицы", "тип панели"},
}

_HEADPHONES_KEYS = {
    "construction_type":  {"конструкция", "тип конструкции"},
    "connection_types":   {"тип подключения", "интерфейс"},
    "has_microphone":     {"наличие микрофона", "микрофон"},
    "noise_cancellation": {"шумоподавление", "активное шумоподавление"},
}

_MICROPHONE_KEYS = {
    "mic_type":         {"тип микрофона", "тип капсюля"},
    "directionality":   {"направленность", "полярная диаграмма"},
    "connection_types": {"тип подключения", "интерфейс"},
    "frequency_range":  {"диапазон частот", "частотный диапазон"},
}

_MOUSEPAD_KEYS = {
    "size":             {"размер", "габариты"},
    "surface_material": {"материал поверхности", "материал"},
    "hardness":         {"жёсткость", "тип поверхности"},
    "has_rgb":          {"подсветка", "rgb-подсветка"},
}


# ── Вспомогательные парсеры значений ──────────────────────────────────────────

def _parse_float(value: str) -> float | None:
    m = re.search(r"[\d]+[.,]?[\d]*", value)
    return float(m.group().replace(",", ".")) if m else None


def _parse_int(value: str) -> int | None:
    m = re.search(r"\d+", value)
    return int(m.group()) if m else None


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in ("да", "есть", "yes", "+", "true")


# ── Общий маппер: options → dict ──────────────────────────────────────────────

def _map_options(options: list[dict], keys_map: dict) -> dict:
    result: dict = {k: None for k in keys_map}
    for opt in options:
        name = opt.get("name", "").lower().strip()
        value = opt.get("value", "").strip()
        for field, key_set in keys_map.items():
            if name in key_set:
                result[field] = value
                break
    return result


# ── Маппер характеристик для каждой категории ─────────────────────────────────

def _map_mouse(options: list[dict]) -> dict:
    raw = _map_options(options, _MOUSE_KEYS)
    weight_str = raw.get("weight")
    weight_g = None
    if weight_str:
        val = _parse_float(weight_str)
        if val is not None:
            weight_g = round(val * 1000) if "кг" in weight_str.lower() else val
    return {
        "weight_g":         weight_g,
        "connection_types": raw.get("connection_types"),
        "sensor":           raw.get("sensor"),
        "switches":         raw.get("switches"),
    }


def _map_keyboard(options: list[dict]) -> dict:
    return _map_options(options, _KEYBOARD_KEYS)


def _map_monitor(options: list[dict]) -> dict:
    raw = _map_options(options, _MONITOR_KEYS)
    return {
        "diagonal_inch":   _parse_float(raw["diagonal_inch"])   if raw["diagonal_inch"]   else None,
        "resolution":      raw["resolution"],
        "refresh_rate_hz": _parse_int(raw["refresh_rate_hz"])   if raw["refresh_rate_hz"] else None,
        "matrix_type":     raw["matrix_type"],
    }


def _map_headphones(options: list[dict]) -> dict:
    raw = _map_options(options, _HEADPHONES_KEYS)
    has_mic_str = raw.get("has_microphone")
    return {
        "construction_type":  raw.get("construction_type"),
        "connection_types":   raw.get("connection_types"),
        "has_microphone":     _parse_bool(has_mic_str) if has_mic_str else False,
        "noise_cancellation": raw.get("noise_cancellation"),
    }


def _map_microphone(options: list[dict]) -> dict:
    return _map_options(options, _MICROPHONE_KEYS)


def _map_mousepad(options: list[dict]) -> dict:
    raw = _map_options(options, _MOUSEPAD_KEYS)
    has_rgb_str = raw.get("has_rgb")
    return {
        "size":             raw.get("size"),
        "surface_material": raw.get("surface_material"),
        "hardness":         raw.get("hardness"),
        "has_rgb":          _parse_bool(has_rgb_str) if has_rgb_str else False,
    }


# ── Извлечение товаров из widgetStates ────────────────────────────────────────

def _extract_products(widget_states: dict) -> list[dict]:
    """Находит виджет с товарами и возвращает плоский список."""
    for key, value in widget_states.items():
        if any(x in key for x in ("searchResultsV2", "tileGrid", "searchResults")):
            try:
                data = json.loads(value)
                items = data.get("items", [])
                if items:
                    return items
            except Exception:
                continue
    return []


# ── Извлечение характеристик из widgetStates товара ───────────────────────────

def _parse_chars_from_widget_states(widget_states: dict) -> list[dict]:
    """Превращает вложенные группы характеристик Ozon в плоский список {name, value}."""
    for key, value in widget_states.items():
        if any(x in key for x in ("webCharacteristics", "webDetailSKU", "characteristics")):
            try:
                data = json.loads(value)
                flat: list[dict] = []
                for group in data.get("characteristics", []):
                    for char in group.get("short_characteristics", []):
                        name = char.get("name", "")
                        vals = char.get("values", [])
                        text = "; ".join(v.get("text", "") for v in vals)
                        flat.append({"name": name, "value": text})
                if flat:
                    return flat
            except Exception:
                continue
    return []


# ── Поиск товаров ─────────────────────────────────────────────────────────────

def _search_ozon(query: str, limit: int = 50) -> list[dict]:
    url = f"/search/?text={quote(query)}&layout_container=categorySearchMegapagination&layout_page_index=1"
    try:
        resp = requests.get(_BASE_URL, params={"url": url}, headers=_HEADERS, timeout=30)
        if resp.status_code != 200:
            return []
        data = resp.json()
        products = _extract_products(data.get("widgetStates", {}))
        return products[:limit]
    except Exception:
        return []


# ── Получение характеристик ───────────────────────────────────────────────────

def _fetch_details(
    product_ids: list[int],
    url_map: dict[int, str],
) -> dict[int, list[dict]]:
    """Для каждого product_id загружает страницу товара и извлекает характеристики."""
    result: dict[int, list[dict]] = {}
    for pid in product_ids:
        product_url = url_map.get(pid)
        if not product_url:
            continue
        try:
            resp = requests.get(
                _BASE_URL,
                params={"url": product_url},
                headers=_HEADERS,
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                chars = _parse_chars_from_widget_states(data.get("widgetStates", {}))
                if chars:
                    result[pid] = chars
        except Exception:
            pass
        time.sleep(random.uniform(0.5, 1.0))
    return result


# ── Единая функция: продукты + характеристики ─────────────────────────────────

def _fetch_all(query: str, limit: int = 50) -> tuple[list[dict], dict[int, list[dict]]]:
    products = _search_ozon(query, limit)
    if not products:
        return [], {}

    url_map: dict[int, str] = {}
    for p in products:
        pid = p.get("id")
        url = p.get("urlForProduct") or p.get("action", {}).get("link", "")
        if pid and url:
            url_map[pid] = url

    details = _fetch_details(list(url_map.keys()), url_map)
    return products, details


# ── Вспомогательные функции извлечения полей товара ───────────────────────────

def _get_price(product: dict) -> float:
    """Извлекает цену из разных возможных полей Ozon."""
    for key in ("finalPrice", "price", "cardPrice"):
        val = product.get(key)
        if val is not None:
            try:
                return float(str(val).replace(" ", "").replace(" ", "").replace(",", "."))
            except ValueError:
                continue
    # Fallback: price may be nested in mainState
    for state in product.get("mainState", []):
        atom = state.get("atom", {})
        price_info = atom.get("price", {})
        if price_info:
            raw = price_info.get("price", "") or price_info.get("originalPrice", "")
            m = re.search(r"[\d]+[.,]?[\d]*", str(raw).replace(" ", ""))
            if m:
                return float(m.group().replace(",", "."))
    return 0.0


def _get_image(product: dict) -> str | None:
    images = product.get("images", [])
    if images:
        return images[0] if isinstance(images[0], str) else images[0].get("url")
    cover = product.get("coverImage")
    return cover if isinstance(cover, str) else None


# ── Общая функция парсинга категории ──────────────────────────────────────────

def _run_parse(db: Session, query: str, model_class, char_mapper) -> dict:
    added = updated = failed = 0
    try:
        products, details = _fetch_all(query)
    except Exception as e:
        return {"added": 0, "updated": 0, "failed": 0, "error": str(e)}

    if not products:
        return {"added": 0, "updated": 0, "failed": 0}

    for product in products:
        try:
            pid = product.get("id")
            if not pid:
                continue
            ozon_sku = str(pid)
            name = product.get("name", "")
            brand = product.get("brand", "")
            price = _get_price(product)
            image_url = _get_image(product)
            product_url = product.get("urlForProduct") or product.get("action", {}).get("link", "")
            ozon_url = f"https://www.ozon.ru{product_url}" if product_url.startswith("/") else product_url

            chars = char_mapper(details.get(pid, []))

            existing = db.query(model_class).filter(model_class.ozon_sku == ozon_sku).first()
            if existing:
                existing.price = price
                if image_url:
                    existing.image_url = image_url
                for field, value in chars.items():
                    if value is not None:
                        setattr(existing, field, value)
                db.commit()
                updated += 1
            else:
                db.add(model_class(
                    name=name,
                    brand=brand,
                    price=price,
                    ozon_sku=ozon_sku,
                    ozon_url=ozon_url,
                    image_url=image_url,
                    **chars,
                ))
                db.commit()
                added += 1
        except Exception:
            failed += 1
            db.rollback()

    return {"added": added, "updated": updated, "failed": failed}


# ── Дочистка: обновить характеристики у существующих записей ──────────────────

def _backfill(db: Session, model_class, char_mapper, null_field: str) -> dict:
    rows = db.query(model_class).filter(
        getattr(model_class, null_field) == None,
        model_class.ozon_sku != None,
    ).all()

    url_map: dict[int, str] = {}
    for row in rows:
        if row.ozon_sku and row.ozon_sku.isdigit() and row.ozon_url:
            pid = int(row.ozon_sku)
            path = row.ozon_url.replace("https://www.ozon.ru", "")
            url_map[pid] = path

    details = _fetch_details(list(url_map.keys()), url_map)
    updated = failed = skipped = 0

    for row in rows:
        if not row.ozon_sku or not row.ozon_sku.isdigit():
            skipped += 1
            continue
        pid = int(row.ozon_sku)
        opts = details.get(pid)
        if not opts:
            skipped += 1
            continue
        try:
            chars = char_mapper(opts)
            for field, value in chars.items():
                if value is not None:
                    setattr(row, field, value)
            db.commit()
            updated += 1
        except Exception:
            failed += 1
            db.rollback()

    return {"updated": updated, "failed": failed, "skipped": skipped}


# ── Публичные функции парсинга ─────────────────────────────────────────────────

def parse_mice(db: Session) -> dict:
    return _run_parse(db, "игровая мышь", Mouse, _map_mouse)

def parse_keyboards(db: Session) -> dict:
    return _run_parse(db, "механическая клавиатура игровая", Keyboard, _map_keyboard)

def parse_monitors(db: Session) -> dict:
    return _run_parse(db, "игровой монитор", Monitor, _map_monitor)

def parse_headphones(db: Session) -> dict:
    return _run_parse(db, "игровые наушники гарнитура", Headphones, _map_headphones)

def parse_microphones(db: Session) -> dict:
    return _run_parse(db, "usb микрофон компьютер", Microphone, _map_microphone)

def parse_mousepads(db: Session) -> dict:
    return _run_parse(db, "игровой коврик для мыши", Mousepad, _map_mousepad)


# ── Дочистка по категориям ────────────────────────────────────────────────────

def backfill_mice(db: Session) -> dict:
    return _backfill(db, Mouse, _map_mouse, "sensor")

def backfill_keyboards(db: Session) -> dict:
    return _backfill(db, Keyboard, _map_keyboard, "switches")

def backfill_monitors(db: Session) -> dict:
    return _backfill(db, Monitor, _map_monitor, "matrix_type")

def backfill_headphones(db: Session) -> dict:
    return _backfill(db, Headphones, _map_headphones, "connection_types")

def backfill_microphones(db: Session) -> dict:
    return _backfill(db, Microphone, _map_microphone, "mic_type")

def backfill_mousepads(db: Session) -> dict:
    return _backfill(db, Mousepad, _map_mousepad, "hardness")
```

- [ ] **Step 2: Run tests**

```
cd backend
.\venv\Scripts\python.exe -m pytest tests/test_ozon_parser.py -x -q
```

Expected: all tests pass.

- [ ] **Step 3: If any mapper test fails, check the key name**

If `test_map_mouse_sensor` fails, it means the field name `"Тип сенсора"` doesn't match the key set. Check `_MOUSE_KEYS["sensor"]` and add the correct name from your probe results.

- [ ] **Step 4: Commit**

```
git add backend/app/parsers/ozon.py backend/tests/test_ozon_parser.py
git commit -m "feat: add Ozon parser with tests"
```

---

## Task 6: Update admin.py and Clean Up

**Files:**
- Modify: `backend/app/routers/admin.py`
- Delete: `backend/app/parsers/wildberries.py`
- Delete: `backend/tests/test_wildberries_parser.py`

- [ ] **Step 1: Replace admin.py**

```python
# backend/app/routers/admin.py
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.parsers.ozon import (
    parse_mice, parse_keyboards, parse_monitors,
    parse_headphones, parse_microphones, parse_mousepads,
    backfill_mice, backfill_keyboards, backfill_monitors,
    backfill_headphones, backfill_microphones, backfill_mousepads,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(x_admin_key: str = Header(...)):
    if x_admin_key != settings.ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/parse/mice", dependencies=[Depends(_require_admin)])
def trigger_parse_mice(db: Session = Depends(get_db)):
    return parse_mice(db)

@router.post("/parse/keyboards", dependencies=[Depends(_require_admin)])
def trigger_parse_keyboards(db: Session = Depends(get_db)):
    return parse_keyboards(db)

@router.post("/parse/monitors", dependencies=[Depends(_require_admin)])
def trigger_parse_monitors(db: Session = Depends(get_db)):
    return parse_monitors(db)

@router.post("/parse/headphones", dependencies=[Depends(_require_admin)])
def trigger_parse_headphones(db: Session = Depends(get_db)):
    return parse_headphones(db)

@router.post("/parse/microphones", dependencies=[Depends(_require_admin)])
def trigger_parse_microphones(db: Session = Depends(get_db)):
    return parse_microphones(db)

@router.post("/parse/mousepads", dependencies=[Depends(_require_admin)])
def trigger_parse_mousepads(db: Session = Depends(get_db)):
    return parse_mousepads(db)


@router.post("/backfill/mice", dependencies=[Depends(_require_admin)])
def trigger_backfill_mice(db: Session = Depends(get_db)):
    return backfill_mice(db)

@router.post("/backfill/keyboards", dependencies=[Depends(_require_admin)])
def trigger_backfill_keyboards(db: Session = Depends(get_db)):
    return backfill_keyboards(db)

@router.post("/backfill/monitors", dependencies=[Depends(_require_admin)])
def trigger_backfill_monitors(db: Session = Depends(get_db)):
    return backfill_monitors(db)

@router.post("/backfill/headphones", dependencies=[Depends(_require_admin)])
def trigger_backfill_headphones(db: Session = Depends(get_db)):
    return backfill_headphones(db)

@router.post("/backfill/microphones", dependencies=[Depends(_require_admin)])
def trigger_backfill_microphones(db: Session = Depends(get_db)):
    return backfill_microphones(db)

@router.post("/backfill/mousepads", dependencies=[Depends(_require_admin)])
def trigger_backfill_mousepads(db: Session = Depends(get_db)):
    return backfill_mousepads(db)
```

- [ ] **Step 2: Delete wildberries.py and old test**

```
Remove-Item backend/app/parsers/wildberries.py
Remove-Item backend/tests/test_wildberries_parser.py
```

- [ ] **Step 3: Run full test suite**

```
cd backend
.\venv\Scripts\python.exe -m pytest tests/ -q
```

Expected: all tests pass, no import errors.

- [ ] **Step 4: Commit**

```
git add -A
git commit -m "refactor: replace WB admin router with Ozon, delete wildberries.py"
```

---

## Task 7: Verify End-to-End

- [ ] **Step 1: Start backend**

```
cd backend
Stop-Process -Name python -ErrorAction SilentlyContinue
Start-Process -FilePath ".\venv\Scripts\uvicorn.exe" -ArgumentList "app.main:app","--host","0.0.0.0","--port","8000" -WorkingDirectory (Get-Location) -WindowStyle Hidden
Start-Sleep -Seconds 3
(Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing).StatusCode
```

Expected: `200`

- [ ] **Step 2: Trigger mice parser**

```
$r = Invoke-WebRequest -Uri "http://localhost:8000/admin/parse/mice" -Method POST -Headers @{"X-Admin-Key"="diplom2026"} -UseBasicParsing -TimeoutSec 300
$r.Content
```

Expected: `{"added": N, "updated": 0, "failed": 0}` where N > 0.

- [ ] **Step 3: Check DB**

```
cd backend
.\venv\Scripts\python.exe -c "
import sys; sys.stdout.reconfigure(encoding='utf-8')
import os; os.environ['DATABASE_URL'] = open('.env').read().split('DATABASE_URL=')[1].split()[0]
from app.database import SessionLocal
from app.models.mouse import Mouse
db = SessionLocal()
mice = db.query(Mouse).limit(5).all()
for m in mice:
    print(f'{m.name[:40]:40} | price={m.price} | sensor={m.sensor} | ozon_sku={m.ozon_sku}')
db.close()
"
```

Expected: rows with `ozon_sku` set, `sensor` populated for most.

- [ ] **Step 4: If sensor/connection_types are null, update key maps**

Run `test_ozon_probe.py` with a real product ID to print all characteristic names. Compare them against `_MOUSE_KEYS` in `ozon.py`. Add any missing names to the key sets. Re-run parser.

- [ ] **Step 5: Final commit**

```
git add -A
git commit -m "feat: Ozon parser working end-to-end"
```
