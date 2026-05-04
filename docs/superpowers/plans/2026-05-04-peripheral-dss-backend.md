# СППР Периферия — Plan 1: Backend + Data Collection

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Построить FastAPI бэкенд с PostgreSQL, парсерами данных (DNS + Wildberries), планировщиком обновлений и движком рекомендаций на основе опросника.

**Architecture:** FastAPI приложение с SQLAlchemy моделями для 6 категорий периферии; два парсера (DNS scraper + WB API) заполняют БД; APScheduler запускает обновления по расписанию; движок рекомендаций переводит ответы пользователя в SQL-фильтры.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL 15, APScheduler 3.x, requests, BeautifulSoup4, pydantic-settings, pytest, httpx (для тестов FastAPI)

---

## Структура файлов

```
backend/
├── app/
│   ├── main.py                  # FastAPI app, подключение роутеров, lifespan
│   ├── config.py                # Настройки через pydantic-settings (.env)
│   ├── database.py              # Движок SQLAlchemy, get_db dependency
│   ├── models/
│   │   ├── __init__.py
│   │   ├── mouse.py
│   │   ├── keyboard.py
│   │   ├── mousepad.py
│   │   ├── monitor.py
│   │   ├── microphone.py
│   │   ├── headphones.py
│   │   └── store_availability.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── mouse.py
│   │   ├── keyboard.py
│   │   ├── mousepad.py
│   │   ├── monitor.py
│   │   ├── microphone.py
│   │   ├── headphones.py
│   │   └── recommendation.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── mice.py
│   │   ├── keyboards.py
│   │   ├── mousepads.py
│   │   ├── monitors.py
│   │   ├── microphones.py
│   │   ├── headphones.py
│   │   ├── recommendation.py
│   │   └── stores.py
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── dns_parser.py        # DNS scraper (категории + наличие по городу)
│   │   ├── wildberries.py       # WB public API client
│   │   └── scheduler.py         # APScheduler задачи
│   └── recommendation/
│       ├── __init__.py
│       ├── questions.py         # Определения вопросов для каждой категории
│       └── engine.py            # Маппинг ответов → SQL-фильтры
├── tests/
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_parsers.py
│   ├── test_recommendation.py
│   └── test_api.py
├── alembic/
│   └── versions/
├── alembic.ini
├── requirements.txt
├── .env.example
└── docker-compose.yml
```

---

## Task 1: Настройка окружения и структуры проекта

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/docker-compose.yml`

- [ ] **Step 1: Создать структуру директорий**

```powershell
cd c:\Users\User\Desktop\diplom
mkdir backend
cd backend
mkdir app, app\models, app\schemas, app\routers, app\parsers, app\recommendation
mkdir tests
mkdir alembic\versions
New-Item app\__init__.py, app\models\__init__.py, app\schemas\__init__.py -ItemType File
New-Item app\routers\__init__.py, app\parsers\__init__.py, app\recommendation\__init__.py -ItemType File
```

- [ ] **Step 2: Создать requirements.txt**

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy==2.0.35
alembic==1.13.3
psycopg2-binary==2.9.9
pydantic-settings==2.5.2
requests==2.32.3
beautifulsoup4==4.12.3
lxml==5.3.0
apscheduler==3.10.4
pytest==8.3.3
httpx==0.27.2
pytest-asyncio==0.24.0
```

- [ ] **Step 3: Создать .env.example**

```
DATABASE_URL=postgresql://postgres:password@localhost:5432/peripheral_dss
DNS_UPDATE_INTERVAL_HOURS=12
WB_UPDATE_INTERVAL_HOURS=12
```

- [ ] **Step 4: Создать docker-compose.yml для PostgreSQL**

```yaml
version: "3.9"
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: peripheral_dss
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
volumes:
  pgdata:
```

- [ ] **Step 5: Создать виртуальное окружение и установить зависимости**

```powershell
cd c:\Users\User\Desktop\diplom\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

- [ ] **Step 6: Запустить PostgreSQL**

```powershell
docker-compose up -d
```

Ожидаемый вывод: `Container backend-db-1 Started`

- [ ] **Step 7: Создать .env из примера**

```powershell
Copy-Item .env.example .env
```

- [ ] **Step 8: Commit**

```powershell
cd c:\Users\User\Desktop\diplom
git init
git add backend/requirements.txt backend/.env.example backend/docker-compose.yml
git commit -m "chore: initial backend project setup"
```

---

## Task 2: Конфигурация и подключение к БД

**Files:**
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`

- [ ] **Step 1: Написать failing тест**

Создать `backend/tests/conftest.py`:
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base

TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def engine():
    eng = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)

@pytest.fixture
def db(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
```

Создать `backend/tests/test_models.py`:
```python
from app.database import Base

def test_base_metadata_exists():
    assert Base.metadata is not None

def test_database_url_loaded():
    from app.config import settings
    assert settings.DATABASE_URL is not None
    assert "postgresql" in settings.DATABASE_URL or "sqlite" in settings.DATABASE_URL
```

- [ ] **Step 2: Запустить тест, убедиться что падает**

```powershell
cd c:\Users\User\Desktop\diplom\backend
venv\Scripts\activate
pytest tests/test_models.py -v
```

Ожидаемый вывод: `FAILED — ModuleNotFoundError: No module named 'app.config'`

- [ ] **Step 3: Создать config.py**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/peripheral_dss"
    DNS_UPDATE_INTERVAL_HOURS: int = 12
    WB_UPDATE_INTERVAL_HOURS: int = 12

    class Config:
        env_file = ".env"

settings = Settings()
```

- [ ] **Step 4: Создать database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 5: Запустить тест, убедиться что проходит**

```powershell
pytest tests/test_models.py -v
```

Ожидаемый вывод: `2 passed`

- [ ] **Step 6: Commit**

```powershell
git add app/config.py app/database.py tests/conftest.py tests/test_models.py
git commit -m "feat: add database connection and settings"
```

---

## Task 3: SQLAlchemy модели

**Files:**
- Create: `backend/app/models/mouse.py`
- Create: `backend/app/models/keyboard.py`
- Create: `backend/app/models/mousepad.py`
- Create: `backend/app/models/monitor.py`
- Create: `backend/app/models/microphone.py`
- Create: `backend/app/models/headphones.py`
- Create: `backend/app/models/store_availability.py`
- Modify: `backend/tests/test_models.py`

- [ ] **Step 1: Написать failing тесты для моделей**

Добавить в `backend/tests/test_models.py`:
```python
from app.models.mouse import Mouse
from app.models.keyboard import Keyboard
from app.models.mousepad import Mousepad
from app.models.monitor import Monitor
from app.models.microphone import Microphone
from app.models.headphones import Headphones
from app.models.store_availability import StoreAvailability

def test_mouse_model_columns(db):
    mouse = Mouse(
        name="Logitech G Pro X Superlight",
        brand="Logitech",
        sensor="HERO 25K",
        switches="Omron D2FC-F-7N",
        weight_g=61.0,
        connection_types="2.4GHz",
        price=8990.0,
    )
    db.add(mouse)
    db.commit()
    db.refresh(mouse)
    assert mouse.id is not None
    assert mouse.name == "Logitech G Pro X Superlight"
    assert mouse.weight_g == 61.0

def test_keyboard_model_columns(db):
    kb = Keyboard(
        name="Keychron K2",
        brand="Keychron",
        switches="Gateron Brown",
        board_material="Aluminum",
        form_factor="TKL",
        keycap_material="PBT",
        keycap_manufacturing="Double-shot",
        connection_types="USB,Bluetooth",
        price=7500.0,
    )
    db.add(kb)
    db.commit()
    db.refresh(kb)
    assert kb.id is not None

def test_monitor_model_columns(db):
    mon = Monitor(
        name='Samsung Odyssey G5 27"',
        brand="Samsung",
        diagonal_inch=27.0,
        resolution="2560x1440",
        refresh_rate_hz=165,
        matrix_type="VA",
        price=28000.0,
    )
    db.add(mon)
    db.commit()
    db.refresh(mon)
    assert mon.id is not None
    assert mon.refresh_rate_hz == 165
```

- [ ] **Step 2: Запустить тесты — убедиться что падают**

```powershell
pytest tests/test_models.py -v
```

Ожидаемый вывод: `FAILED — ModuleNotFoundError: No module named 'app.models.mouse'`

- [ ] **Step 3: Создать базовый mixin в models/__init__.py**

```python
from app.database import Base
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func

class TimestampMixin:
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

- [ ] **Step 4: Создать models/mouse.py**

```python
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
    connection_types = Column(String)   # "USB,2.4GHz,Bluetooth"
    price = Column(Float)
    dns_product_id = Column(String, unique=True, nullable=True)
    wb_sku = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    dns_url = Column(String, nullable=True)
    wb_url = Column(String, nullable=True)
```

- [ ] **Step 5: Создать models/keyboard.py**

```python
from sqlalchemy import Column, Integer, String, Float
from app.database import Base
from app.models import TimestampMixin

class Keyboard(Base, TimestampMixin):
    __tablename__ = "keyboards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String)
    switches = Column(String)           # "Gateron Brown, Cherry MX Red"
    board_material = Column(String)     # "Plastic, Aluminum"
    form_factor = Column(String)        # "Full-size, TKL, 65%, 60%"
    keycap_material = Column(String)    # "ABS, PBT"
    keycap_manufacturing = Column(String)  # "Double-shot, Dye-sub"
    connection_types = Column(String)   # "USB,Bluetooth,2.4GHz"
    price = Column(Float)
    dns_product_id = Column(String, unique=True, nullable=True)
    wb_sku = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    dns_url = Column(String, nullable=True)
    wb_url = Column(String, nullable=True)
```

- [ ] **Step 6: Создать models/mousepad.py**

```python
from sqlalchemy import Column, Integer, String, Float, Boolean
from app.database import Base
from app.models import TimestampMixin

class Mousepad(Base, TimestampMixin):
    __tablename__ = "mousepads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String)
    size = Column(String)               # "S, M, L, XL"
    surface_material = Column(String)   # "Fabric, Plastic, Leather"
    hardness = Column(String)           # "Soft, Hard"
    has_rgb = Column(Boolean, default=False)
    price = Column(Float)
    dns_product_id = Column(String, unique=True, nullable=True)
    wb_sku = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    dns_url = Column(String, nullable=True)
    wb_url = Column(String, nullable=True)
```

- [ ] **Step 7: Создать models/monitor.py**

```python
from sqlalchemy import Column, Integer, String, Float
from app.database import Base
from app.models import TimestampMixin

class Monitor(Base, TimestampMixin):
    __tablename__ = "monitors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String)
    diagonal_inch = Column(Float)
    resolution = Column(String)         # "1920x1080, 2560x1440, 3840x2160"
    refresh_rate_hz = Column(Integer)
    matrix_type = Column(String)        # "IPS, VA, TN, OLED"
    price = Column(Float)
    dns_product_id = Column(String, unique=True, nullable=True)
    wb_sku = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    dns_url = Column(String, nullable=True)
    wb_url = Column(String, nullable=True)
```

- [ ] **Step 8: Создать models/microphone.py**

```python
from sqlalchemy import Column, Integer, String, Float
from app.database import Base
from app.models import TimestampMixin

class Microphone(Base, TimestampMixin):
    __tablename__ = "microphones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String)
    mic_type = Column(String)           # "Condenser, Dynamic"
    directionality = Column(String)     # "Cardioid, Omnidirectional, Bidirectional"
    connection_types = Column(String)   # "USB,XLR,3.5mm"
    frequency_range = Column(String)    # "20Hz-20kHz"
    price = Column(Float)
    dns_product_id = Column(String, unique=True, nullable=True)
    wb_sku = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    dns_url = Column(String, nullable=True)
    wb_url = Column(String, nullable=True)
```

- [ ] **Step 9: Создать models/headphones.py**

```python
from sqlalchemy import Column, Integer, String, Float, Boolean
from app.database import Base
from app.models import TimestampMixin

class Headphones(Base, TimestampMixin):
    __tablename__ = "headphones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String)
    construction_type = Column(String)  # "Over-ear, On-ear, In-ear"
    connection_types = Column(String)   # "Wired,Wireless,USB"
    has_microphone = Column(Boolean, default=False)
    noise_cancellation = Column(String) # "Active, Passive, None"
    price = Column(Float)
    dns_product_id = Column(String, unique=True, nullable=True)
    wb_sku = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    dns_url = Column(String, nullable=True)
    wb_url = Column(String, nullable=True)
```

- [ ] **Step 10: Создать models/store_availability.py**

```python
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from app.database import Base

class StoreAvailability(Base):
    __tablename__ = "store_availability"

    id = Column(Integer, primary_key=True, index=True)
    product_type = Column(String, nullable=False)   # "mouse", "keyboard", etc.
    product_id = Column(Integer, nullable=False)
    dns_product_id = Column(String, nullable=False)
    city = Column(String, nullable=False)
    store_address = Column(String, nullable=False)
    store_name = Column(String, nullable=True)
    in_stock = Column(Boolean, default=True)
```

- [ ] **Step 11: Запустить тесты**

```powershell
pytest tests/test_models.py -v
```

Ожидаемый вывод: `5 passed`

- [ ] **Step 12: Commit**

```powershell
git add app/models/
git commit -m "feat: add SQLAlchemy models for all peripheral categories"
```

---

## Task 4: Alembic миграции

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`

- [ ] **Step 1: Инициализировать Alembic**

```powershell
cd c:\Users\User\Desktop\diplom\backend
venv\Scripts\activate
alembic init alembic
```

- [ ] **Step 2: Настроить alembic/env.py — найти строку с target_metadata и заменить блок**

В файле `alembic/env.py` найти строки:
```python
# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = None
```

Заменить на:
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database import Base
from app.models.mouse import Mouse
from app.models.keyboard import Keyboard
from app.models.mousepad import Mousepad
from app.models.monitor import Monitor
from app.models.microphone import Microphone
from app.models.headphones import Headphones
from app.models.store_availability import StoreAvailability

target_metadata = Base.metadata
```

- [ ] **Step 3: Настроить alembic.ini — заменить строку с sqlalchemy.url**

В `alembic.ini` найти:
```
sqlalchemy.url = driver://user:pass@localhost/dbname
```

Заменить на:
```
sqlalchemy.url = postgresql://postgres:password@localhost:5432/peripheral_dss
```

- [ ] **Step 4: Создать первую миграцию**

```powershell
alembic revision --autogenerate -m "initial tables"
```

Ожидаемый вывод: `Generating .../alembic/versions/xxxx_initial_tables.py ... done`

- [ ] **Step 5: Применить миграцию**

```powershell
alembic upgrade head
```

Ожидаемый вывод: `Running upgrade -> xxxx, initial tables`

- [ ] **Step 6: Commit**

```powershell
git add alembic/ alembic.ini
git commit -m "feat: add alembic migrations for all tables"
```

---

## Task 5: Pydantic схемы

**Files:**
- Create: `backend/app/schemas/mouse.py`
- Create: `backend/app/schemas/keyboard.py`
- Create: `backend/app/schemas/mousepad.py`
- Create: `backend/app/schemas/monitor.py`
- Create: `backend/app/schemas/microphone.py`
- Create: `backend/app/schemas/headphones.py`
- Create: `backend/app/schemas/recommendation.py`

- [ ] **Step 1: Создать schemas/mouse.py**

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MouseResponse(BaseModel):
    id: int
    name: str
    brand: Optional[str] = None
    sensor: Optional[str] = None
    switches: Optional[str] = None
    weight_g: Optional[float] = None
    connection_types: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    dns_url: Optional[str] = None
    wb_url: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class MouseCreate(BaseModel):
    name: str
    brand: Optional[str] = None
    sensor: Optional[str] = None
    switches: Optional[str] = None
    weight_g: Optional[float] = None
    connection_types: Optional[str] = None
    price: Optional[float] = None
    dns_product_id: Optional[str] = None
    wb_sku: Optional[str] = None
    image_url: Optional[str] = None
    dns_url: Optional[str] = None
    wb_url: Optional[str] = None
```

- [ ] **Step 2: Создать schemas/keyboard.py**

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class KeyboardResponse(BaseModel):
    id: int
    name: str
    brand: Optional[str] = None
    switches: Optional[str] = None
    board_material: Optional[str] = None
    form_factor: Optional[str] = None
    keycap_material: Optional[str] = None
    keycap_manufacturing: Optional[str] = None
    connection_types: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    dns_url: Optional[str] = None
    wb_url: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class KeyboardCreate(BaseModel):
    name: str
    brand: Optional[str] = None
    switches: Optional[str] = None
    board_material: Optional[str] = None
    form_factor: Optional[str] = None
    keycap_material: Optional[str] = None
    keycap_manufacturing: Optional[str] = None
    connection_types: Optional[str] = None
    price: Optional[float] = None
    dns_product_id: Optional[str] = None
    wb_sku: Optional[str] = None
    image_url: Optional[str] = None
    dns_url: Optional[str] = None
    wb_url: Optional[str] = None
```

- [ ] **Step 3: Создать schemas/mousepad.py**

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MousepadResponse(BaseModel):
    id: int
    name: str
    brand: Optional[str] = None
    size: Optional[str] = None
    surface_material: Optional[str] = None
    hardness: Optional[str] = None
    has_rgb: Optional[bool] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    dns_url: Optional[str] = None
    wb_url: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class MousepadCreate(BaseModel):
    name: str
    brand: Optional[str] = None
    size: Optional[str] = None
    surface_material: Optional[str] = None
    hardness: Optional[str] = None
    has_rgb: Optional[bool] = None
    price: Optional[float] = None
    dns_product_id: Optional[str] = None
    wb_sku: Optional[str] = None
    image_url: Optional[str] = None
    dns_url: Optional[str] = None
    wb_url: Optional[str] = None
```

- [ ] **Step 4: Создать schemas/monitor.py**

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MonitorResponse(BaseModel):
    id: int
    name: str
    brand: Optional[str] = None
    diagonal_inch: Optional[float] = None
    resolution: Optional[str] = None
    refresh_rate_hz: Optional[int] = None
    matrix_type: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    dns_url: Optional[str] = None
    wb_url: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class MonitorCreate(BaseModel):
    name: str
    brand: Optional[str] = None
    diagonal_inch: Optional[float] = None
    resolution: Optional[str] = None
    refresh_rate_hz: Optional[int] = None
    matrix_type: Optional[str] = None
    price: Optional[float] = None
    dns_product_id: Optional[str] = None
    wb_sku: Optional[str] = None
    image_url: Optional[str] = None
    dns_url: Optional[str] = None
    wb_url: Optional[str] = None
```

- [ ] **Step 5: Создать schemas/microphone.py**

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MicrophoneResponse(BaseModel):
    id: int
    name: str
    brand: Optional[str] = None
    mic_type: Optional[str] = None
    directionality: Optional[str] = None
    connection_types: Optional[str] = None
    frequency_range: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    dns_url: Optional[str] = None
    wb_url: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class MicrophoneCreate(BaseModel):
    name: str
    brand: Optional[str] = None
    mic_type: Optional[str] = None
    directionality: Optional[str] = None
    connection_types: Optional[str] = None
    frequency_range: Optional[str] = None
    price: Optional[float] = None
    dns_product_id: Optional[str] = None
    wb_sku: Optional[str] = None
    image_url: Optional[str] = None
    dns_url: Optional[str] = None
    wb_url: Optional[str] = None
```

- [ ] **Step 6: Создать schemas/headphones.py**

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class HeadphonesResponse(BaseModel):
    id: int
    name: str
    brand: Optional[str] = None
    construction_type: Optional[str] = None
    connection_types: Optional[str] = None
    has_microphone: Optional[bool] = None
    noise_cancellation: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    dns_url: Optional[str] = None
    wb_url: Optional[str] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class HeadphonesCreate(BaseModel):
    name: str
    brand: Optional[str] = None
    construction_type: Optional[str] = None
    connection_types: Optional[str] = None
    has_microphone: Optional[bool] = None
    noise_cancellation: Optional[str] = None
    price: Optional[float] = None
    dns_product_id: Optional[str] = None
    wb_sku: Optional[str] = None
    image_url: Optional[str] = None
    dns_url: Optional[str] = None
    wb_url: Optional[str] = None
```

- [ ] **Step 7: Создать schemas/recommendation.py**

```python
from pydantic import BaseModel
from typing import Dict, List, Any

class QuestionOption(BaseModel):
    value: str
    label: str

class Question(BaseModel):
    id: str
    text: str
    options: List[QuestionOption]

class RecommendationRequest(BaseModel):
    category: str                    # "mouse", "keyboard", etc.
    answers: Dict[str, str]          # {"use_case": "gaming", "budget": "mid"}

class StoreInfo(BaseModel):
    store_name: str
    store_address: str
    city: str
    in_stock: bool
```

- [ ] **Step 8: Commit**

```powershell
git add app/schemas/
git commit -m "feat: add pydantic schemas for all categories"
```

---

## Task 6: FastAPI роутеры для всех категорий

**Files:**
- Create: `backend/app/routers/mice.py`
- Create: `backend/app/routers/keyboards.py`
- Create: `backend/app/routers/mousepads.py`
- Create: `backend/app/routers/monitors.py`
- Create: `backend/app/routers/microphones.py`
- Create: `backend/app/routers/headphones.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/test_api.py`

- [ ] **Step 1: Написать failing API тесты**

Создать `backend/tests/test_api.py`:
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

TEST_DATABASE_URL = "sqlite:///./test_api.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_get_mice_empty():
    response = client.get("/mice/")
    assert response.status_code == 200
    assert response.json() == []

def test_get_keyboards_empty():
    response = client.get("/keyboards/")
    assert response.status_code == 200
    assert response.json() == []

def test_get_monitors_empty():
    response = client.get("/monitors/")
    assert response.status_code == 200
    assert response.json() == []

def test_mice_filter_by_price():
    response = client.get("/mice/?price_max=5000")
    assert response.status_code == 200

def test_keyboards_filter_by_form_factor():
    response = client.get("/keyboards/?form_factor=TKL")
    assert response.status_code == 200

def test_monitors_filter_by_matrix():
    response = client.get("/monitors/?matrix_type=IPS")
    assert response.status_code == 200
```

- [ ] **Step 2: Запустить тесты — убедиться что падают**

```powershell
pytest tests/test_api.py -v
```

Ожидаемый вывод: `FAILED — ModuleNotFoundError: No module named 'app.main'`

- [ ] **Step 3: Создать routers/mice.py**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.mouse import Mouse
from app.schemas.mouse import MouseResponse

router = APIRouter(prefix="/mice", tags=["mice"])

@router.get("/", response_model=List[MouseResponse])
def list_mice(
    sensor: Optional[str] = None,
    connection: Optional[str] = None,
    weight_max: Optional[float] = None,
    price_max: Optional[float] = None,
    price_min: Optional[float] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Mouse)
    if sensor:
        query = query.filter(Mouse.sensor == sensor)
    if connection:
        query = query.filter(Mouse.connection_types.contains(connection))
    if weight_max:
        query = query.filter(Mouse.weight_g <= weight_max)
    if price_max:
        query = query.filter(Mouse.price <= price_max)
    if price_min:
        query = query.filter(Mouse.price >= price_min)
    return query.all()

@router.get("/{mouse_id}", response_model=MouseResponse)
def get_mouse(mouse_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    mouse = db.query(Mouse).filter(Mouse.id == mouse_id).first()
    if not mouse:
        raise HTTPException(status_code=404, detail="Mouse not found")
    return mouse
```

- [ ] **Step 4: Создать routers/keyboards.py**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.keyboard import Keyboard
from app.schemas.keyboard import KeyboardResponse

router = APIRouter(prefix="/keyboards", tags=["keyboards"])

@router.get("/", response_model=List[KeyboardResponse])
def list_keyboards(
    switches: Optional[str] = None,
    form_factor: Optional[str] = None,
    connection: Optional[str] = None,
    keycap_material: Optional[str] = None,
    price_max: Optional[float] = None,
    price_min: Optional[float] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Keyboard)
    if switches:
        query = query.filter(Keyboard.switches.contains(switches))
    if form_factor:
        query = query.filter(Keyboard.form_factor == form_factor)
    if connection:
        query = query.filter(Keyboard.connection_types.contains(connection))
    if keycap_material:
        query = query.filter(Keyboard.keycap_material == keycap_material)
    if price_max:
        query = query.filter(Keyboard.price <= price_max)
    if price_min:
        query = query.filter(Keyboard.price >= price_min)
    return query.all()

@router.get("/{keyboard_id}", response_model=KeyboardResponse)
def get_keyboard(keyboard_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    kb = db.query(Keyboard).filter(Keyboard.id == keyboard_id).first()
    if not kb:
        raise HTTPException(status_code=404, detail="Keyboard not found")
    return kb
```

- [ ] **Step 5: Создать routers/mousepads.py**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.mousepad import Mousepad
from app.schemas.mousepad import MousepadResponse

router = APIRouter(prefix="/mousepads", tags=["mousepads"])

@router.get("/", response_model=List[MousepadResponse])
def list_mousepads(
    size: Optional[str] = None,
    surface_material: Optional[str] = None,
    hardness: Optional[str] = None,
    has_rgb: Optional[bool] = None,
    price_max: Optional[float] = None,
    price_min: Optional[float] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Mousepad)
    if size:
        query = query.filter(Mousepad.size == size)
    if surface_material:
        query = query.filter(Mousepad.surface_material == surface_material)
    if hardness:
        query = query.filter(Mousepad.hardness == hardness)
    if has_rgb is not None:
        query = query.filter(Mousepad.has_rgb == has_rgb)
    if price_max:
        query = query.filter(Mousepad.price <= price_max)
    if price_min:
        query = query.filter(Mousepad.price >= price_min)
    return query.all()

@router.get("/{pad_id}", response_model=MousepadResponse)
def get_mousepad(pad_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    pad = db.query(Mousepad).filter(Mousepad.id == pad_id).first()
    if not pad:
        raise HTTPException(status_code=404, detail="Mousepad not found")
    return pad
```

- [ ] **Step 6: Создать routers/monitors.py**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.monitor import Monitor
from app.schemas.monitor import MonitorResponse

router = APIRouter(prefix="/monitors", tags=["monitors"])

@router.get("/", response_model=List[MonitorResponse])
def list_monitors(
    diagonal_min: Optional[float] = None,
    diagonal_max: Optional[float] = None,
    resolution: Optional[str] = None,
    refresh_rate_min: Optional[int] = None,
    matrix_type: Optional[str] = None,
    price_max: Optional[float] = None,
    price_min: Optional[float] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Monitor)
    if diagonal_min:
        query = query.filter(Monitor.diagonal_inch >= diagonal_min)
    if diagonal_max:
        query = query.filter(Monitor.diagonal_inch <= diagonal_max)
    if resolution:
        query = query.filter(Monitor.resolution == resolution)
    if refresh_rate_min:
        query = query.filter(Monitor.refresh_rate_hz >= refresh_rate_min)
    if matrix_type:
        query = query.filter(Monitor.matrix_type == matrix_type)
    if price_max:
        query = query.filter(Monitor.price <= price_max)
    if price_min:
        query = query.filter(Monitor.price >= price_min)
    return query.all()

@router.get("/{monitor_id}", response_model=MonitorResponse)
def get_monitor(monitor_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    mon = db.query(Monitor).filter(Monitor.id == monitor_id).first()
    if not mon:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return mon
```

- [ ] **Step 7: Создать routers/microphones.py**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.microphone import Microphone
from app.schemas.microphone import MicrophoneResponse

router = APIRouter(prefix="/microphones", tags=["microphones"])

@router.get("/", response_model=List[MicrophoneResponse])
def list_microphones(
    mic_type: Optional[str] = None,
    directionality: Optional[str] = None,
    connection: Optional[str] = None,
    price_max: Optional[float] = None,
    price_min: Optional[float] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Microphone)
    if mic_type:
        query = query.filter(Microphone.mic_type == mic_type)
    if directionality:
        query = query.filter(Microphone.directionality == directionality)
    if connection:
        query = query.filter(Microphone.connection_types.contains(connection))
    if price_max:
        query = query.filter(Microphone.price <= price_max)
    if price_min:
        query = query.filter(Microphone.price >= price_min)
    return query.all()

@router.get("/{mic_id}", response_model=MicrophoneResponse)
def get_microphone(mic_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    mic = db.query(Microphone).filter(Microphone.id == mic_id).first()
    if not mic:
        raise HTTPException(status_code=404, detail="Microphone not found")
    return mic
```

- [ ] **Step 8: Создать routers/headphones.py**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.headphones import Headphones
from app.schemas.headphones import HeadphonesResponse

router = APIRouter(prefix="/headphones", tags=["headphones"])

@router.get("/", response_model=List[HeadphonesResponse])
def list_headphones(
    construction_type: Optional[str] = None,
    connection: Optional[str] = None,
    has_microphone: Optional[bool] = None,
    noise_cancellation: Optional[str] = None,
    price_max: Optional[float] = None,
    price_min: Optional[float] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Headphones)
    if construction_type:
        query = query.filter(Headphones.construction_type == construction_type)
    if connection:
        query = query.filter(Headphones.connection_types.contains(connection))
    if has_microphone is not None:
        query = query.filter(Headphones.has_microphone == has_microphone)
    if noise_cancellation:
        query = query.filter(Headphones.noise_cancellation == noise_cancellation)
    if price_max:
        query = query.filter(Headphones.price <= price_max)
    if price_min:
        query = query.filter(Headphones.price >= price_min)
    return query.all()

@router.get("/{headphones_id}", response_model=HeadphonesResponse)
def get_headphones(headphones_id: int, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    hp = db.query(Headphones).filter(Headphones.id == headphones_id).first()
    if not hp:
        raise HTTPException(status_code=404, detail="Headphones not found")
    return hp
```

- [ ] **Step 9: Создать main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import mice, keyboards, mousepads, monitors, microphones, headphones

app = FastAPI(title="Peripheral DSS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],   # React dev server
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

@app.get("/")
def root():
    return {"message": "Peripheral DSS API"}
```

- [ ] **Step 10: Запустить тесты**

```powershell
pytest tests/test_api.py -v
```

Ожидаемый вывод: `6 passed`

- [ ] **Step 11: Запустить сервер и проверить документацию**

```powershell
uvicorn app.main:app --reload
```

Открыть в браузере: `http://localhost:8000/docs` — должна открыться Swagger UI со всеми роутами.

- [ ] **Step 12: Commit**

```powershell
git add app/routers/ app/main.py tests/test_api.py
git commit -m "feat: add CRUD API endpoints for all peripheral categories"
```

---

## Task 7: DNS парсер

**Files:**
- Create: `backend/app/parsers/dns_parser.py`
- Create: `backend/tests/test_parsers.py`

> DNS категории: мышки — `/catalog/17a8a01d16404e77/myshi/`, клавиатуры — `/catalog/17a8a016164b4e77/klaviatury/`, коврики — `/catalog/17a8a02116404e77/kovriki-dlya-myshi/`, мониторы — `/catalog/17a8a0d016404e77/monitory/`, микрофоны — `/catalog/17a8a0e716404e77/mikrofony/`, наушники — `/catalog/17a8a01f16404e77/naushniki/`

- [ ] **Step 1: Написать failing тесты для парсера**

Создать `backend/tests/test_parsers.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from app.parsers.dns_parser import DNSParser

def test_dns_parser_init():
    parser = DNSParser()
    assert parser.base_url == "https://www.dns-shop.ru"
    assert "mouse" in parser.category_urls

def test_dns_parser_has_all_categories():
    parser = DNSParser()
    categories = ["mouse", "keyboard", "mousepad", "monitor", "microphone", "headphones"]
    for cat in categories:
        assert cat in parser.category_urls, f"Missing category: {cat}"

def test_build_store_url():
    parser = DNSParser()
    url = parser._build_product_url("abc123")
    assert "abc123" in url
    assert url.startswith("https://")
```

- [ ] **Step 2: Запустить тесты — убедиться что падают**

```powershell
pytest tests/test_parsers.py -v
```

Ожидаемый вывод: `FAILED — ModuleNotFoundError: No module named 'app.parsers.dns_parser'`

- [ ] **Step 3: Создать parsers/dns_parser.py**

```python
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import time
import logging

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9",
}

class DNSParser:
    base_url = "https://www.dns-shop.ru"

    category_urls = {
        "mouse":       "/catalog/17a8a01d16404e77/myshi/",
        "keyboard":    "/catalog/17a8a016164b4e77/klaviatury/",
        "mousepad":    "/catalog/17a8a02116404e77/kovriki-dlya-myshi/",
        "monitor":     "/catalog/17a8a0d016404e77/monitory/",
        "microphone":  "/catalog/17a8a0e716404e77/mikrofony/",
        "headphones":  "/catalog/17a8a01f16404e77/naushniki/",
    }

    def _build_product_url(self, product_id: str) -> str:
        return f"{self.base_url}/product/{product_id}/"

    def _get(self, url: str) -> Optional[BeautifulSoup]:
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.text, "lxml")
        except requests.RequestException as e:
            logger.error(f"DNS request failed for {url}: {e}")
            return None

    def fetch_products(self, category: str, pages: int = 3) -> List[Dict]:
        """Получить список товаров из категории DNS."""
        if category not in self.category_urls:
            raise ValueError(f"Unknown category: {category}")

        products = []
        for page in range(1, pages + 1):
            url = f"{self.base_url}{self.category_urls[category]}?p={page}"
            soup = self._get(url)
            if not soup:
                break

            items = soup.select("div.catalog-product")
            if not items:
                break

            for item in items:
                product = self._parse_product_card(item)
                if product:
                    products.append(product)

            time.sleep(1)   # вежливая задержка

        return products

    def _parse_product_card(self, item) -> Optional[Dict]:
        try:
            name_tag = item.select_one("a.catalog-product__name")
            price_tag = item.select_one("div.product-buy__price")
            img_tag = item.select_one("img.catalog-product__image")

            if not name_tag:
                return None

            name = name_tag.get_text(strip=True)
            href = name_tag.get("href", "")
            product_id = href.strip("/").split("/")[-1] if href else None
            price_text = price_tag.get_text(strip=True) if price_tag else "0"
            price = float("".join(filter(str.isdigit, price_text)) or 0)
            image_url = img_tag.get("src") if img_tag else None

            return {
                "name": name,
                "price": price,
                "dns_product_id": product_id,
                "dns_url": f"{self.base_url}{href}",
                "image_url": image_url,
            }
        except Exception as e:
            logger.error(f"Error parsing product card: {e}")
            return None

    def fetch_store_availability(self, dns_product_id: str, city: str) -> List[Dict]:
        """Получить список магазинов DNS с наличием товара в указанном городе."""
        url = f"{self.base_url}/product/{dns_product_id}/buy/"
        soup = self._get(url)
        if not soup:
            return []

        stores = []
        city_lower = city.lower()

        store_items = soup.select("div.buy-in-store-item, li.store-item")
        for store in store_items:
            address_tag = store.select_one(".store-address, .buy-in-store__address")
            name_tag = store.select_one(".store-name, .buy-in-store__name")
            stock_tag = store.select_one(".store-stock, .buy-in-store__count")

            if not address_tag:
                continue

            address = address_tag.get_text(strip=True)
            if city_lower not in address.lower():
                continue

            stores.append({
                "store_name": name_tag.get_text(strip=True) if name_tag else "DNS",
                "store_address": address,
                "city": city,
                "in_stock": bool(stock_tag and "нет" not in stock_tag.get_text(strip=True).lower()),
            })

        return stores
```

- [ ] **Step 4: Запустить тесты**

```powershell
pytest tests/test_parsers.py -v
```

Ожидаемый вывод: `3 passed`

- [ ] **Step 5: Commit**

```powershell
git add app/parsers/dns_parser.py tests/test_parsers.py
git commit -m "feat: add DNS parser for product listings and store availability"
```

---

## Task 8: Wildberries API клиент

**Files:**
- Create: `backend/app/parsers/wildberries.py`
- Modify: `backend/tests/test_parsers.py`

- [ ] **Step 1: Написать failing тест**

Добавить в `backend/tests/test_parsers.py`:
```python
from app.parsers.wildberries import WildberriesClient

def test_wb_client_init():
    client = WildberriesClient()
    assert client.search_url.startswith("https://")

def test_wb_build_product_url():
    client = WildberriesClient()
    url = client._build_product_url("12345678")
    assert "12345678" in url
    assert url.startswith("https://")
```

- [ ] **Step 2: Запустить тест — убедиться что падает**

```powershell
pytest tests/test_parsers.py::test_wb_client_init -v
```

Ожидаемый вывод: `FAILED — ModuleNotFoundError`

- [ ] **Step 3: Создать parsers/wildberries.py**

```python
import requests
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

CATEGORY_QUERIES = {
    "mouse":       "игровая мышь",
    "keyboard":    "механическая клавиатура",
    "mousepad":    "коврик для мыши",
    "monitor":     "монитор для ПК",
    "microphone":  "USB микрофон",
    "headphones":  "наушники для компьютера",
}

class WildberriesClient:
    search_url = "https://search.wb.ru/exactmatch/ru/common/v4/search"
    detail_url = "https://card.wb.ru/cards/v1/detail"

    def _build_product_url(self, sku: str) -> str:
        return f"https://www.wildberries.ru/catalog/{sku}/detail.aspx"

    def _search(self, query: str, limit: int = 50) -> List[Dict]:
        params = {
            "appType": "1",
            "curr": "rub",
            "dest": "-1257786",
            "query": query,
            "resultset": "catalog",
            "sort": "popular",
            "suppressSpellcheck": "false",
        }
        try:
            response = requests.get(self.search_url, params=params, headers=HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()
            products = data.get("data", {}).get("products", [])
            return products[:limit]
        except (requests.RequestException, ValueError) as e:
            logger.error(f"WB search failed for '{query}': {e}")
            return []

    def fetch_products(self, category: str, limit: int = 50) -> List[Dict]:
        """Получить список товаров WB для категории."""
        if category not in CATEGORY_QUERIES:
            raise ValueError(f"Unknown category: {category}")

        raw_products = self._search(CATEGORY_QUERIES[category], limit)
        products = []

        for item in raw_products:
            sku = str(item.get("id", ""))
            name = item.get("name", "")
            brand = item.get("brand", "")
            price_raw = item.get("priceU", 0)
            price = price_raw / 100 if price_raw else 0
            image_url = self._build_image_url(sku)

            products.append({
                "name": f"{brand} {name}".strip(),
                "brand": brand,
                "price": price,
                "wb_sku": sku,
                "wb_url": self._build_product_url(sku),
                "image_url": image_url,
            })

        return products

    def _build_image_url(self, sku: str) -> str:
        vol = int(sku) // 100000
        part = int(sku) // 1000
        return f"https://basket-{vol % 20 + 1:02d}.wbbasket.ru/vol{vol}/part{part}/{sku}/images/c516x688/1.jpg"
```

- [ ] **Step 4: Запустить тесты**

```powershell
pytest tests/test_parsers.py -v
```

Ожидаемый вывод: `5 passed`

- [ ] **Step 5: Commit**

```powershell
git add app/parsers/wildberries.py
git commit -m "feat: add Wildberries API client for product search"
```

---

## Task 9: Планировщик обновлений и роутер обновления данных

**Files:**
- Create: `backend/app/parsers/scheduler.py`
- Create: `backend/app/routers/admin.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Создать parsers/scheduler.py**

```python
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.parsers.dns_parser import DNSParser
from app.parsers.wildberries import WildberriesClient
from app.models.mouse import Mouse
from app.models.keyboard import Keyboard
from app.models.mousepad import Mousepad
from app.models.monitor import Monitor
from app.models.microphone import Microphone
from app.models.headphones import Headphones
import logging

logger = logging.getLogger(__name__)

MODEL_MAP = {
    "mouse": Mouse,
    "keyboard": Keyboard,
    "mousepad": Mousepad,
    "monitor": Monitor,
    "microphone": Microphone,
    "headphones": Headphones,
}

def upsert_dns_products(category: str, db: Session):
    parser = DNSParser()
    products = parser.fetch_products(category, pages=2)
    model = MODEL_MAP[category]

    for p in products:
        dns_id = p.get("dns_product_id")
        if not dns_id:
            continue
        existing = db.query(model).filter(model.dns_product_id == dns_id).first()
        if existing:
            existing.price = p.get("price", existing.price)
            existing.image_url = p.get("image_url", existing.image_url)
        else:
            obj = model(
                name=p["name"],
                price=p.get("price"),
                dns_product_id=dns_id,
                dns_url=p.get("dns_url"),
                image_url=p.get("image_url"),
            )
            db.add(obj)
    db.commit()
    logger.info(f"DNS update done for category: {category}, {len(products)} products")

def upsert_wb_products(category: str, db: Session):
    client = WildberriesClient()
    products = client.fetch_products(category, limit=30)
    model = MODEL_MAP[category]

    for p in products:
        sku = p.get("wb_sku")
        if not sku:
            continue
        existing = db.query(model).filter(model.wb_sku == sku).first()
        if existing:
            existing.price = p.get("price", existing.price)
        else:
            obj = model(
                name=p["name"],
                brand=p.get("brand"),
                price=p.get("price"),
                wb_sku=sku,
                wb_url=p.get("wb_url"),
                image_url=p.get("image_url"),
            )
            db.add(obj)
    db.commit()
    logger.info(f"WB update done for category: {category}, {len(products)} products")

def run_all_updates():
    db = SessionLocal()
    try:
        for category in MODEL_MAP:
            upsert_dns_products(category, db)
            upsert_wb_products(category, db)
    finally:
        db.close()

def create_scheduler(interval_hours: int = 12) -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_all_updates, "interval", hours=interval_hours, id="data_update")
    return scheduler
```

- [ ] **Step 2: Создать routers/admin.py (эндпоинт для ручного запуска обновления)**

```python
from fastapi import APIRouter, BackgroundTasks
from app.parsers.scheduler import run_all_updates

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/update-data")
def trigger_update(background_tasks: BackgroundTasks):
    """Запустить принудительное обновление данных из DNS и WB."""
    background_tasks.add_task(run_all_updates)
    return {"message": "Data update started in background"}

@router.get("/update-status")
def update_status():
    return {"status": "Use POST /admin/update-data to trigger update"}
```

- [ ] **Step 3: Обновить main.py — добавить планировщик и admin роутер**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import mice, keyboards, mousepads, monitors, microphones, headphones
from app.routers import admin
from app.parsers.scheduler import create_scheduler
from app.config import settings

scheduler = create_scheduler(settings.DNS_UPDATE_INTERVAL_HOURS)

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(title="Peripheral DSS API", version="1.0.0", lifespan=lifespan)

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
app.include_router(admin.router)

@app.get("/")
def root():
    return {"message": "Peripheral DSS API"}
```

- [ ] **Step 4: Запустить сервер и проверить эндпоинт**

```powershell
uvicorn app.main:app --reload
```

В отдельном терминале:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/admin/update-data" -Method POST
```

Ожидаемый ответ: `{"message": "Data update started in background"}`

- [ ] **Step 5: Commit**

```powershell
git add app/parsers/scheduler.py app/routers/admin.py app/main.py
git commit -m "feat: add data update scheduler and admin trigger endpoint"
```

---

## Task 10: Движок рекомендаций

**Files:**
- Create: `backend/app/recommendation/questions.py`
- Create: `backend/app/recommendation/engine.py`
- Create: `backend/app/routers/recommendation.py`
- Create: `backend/tests/test_recommendation.py`

- [ ] **Step 1: Написать failing тесты**

Создать `backend/tests/test_recommendation.py`:
```python
from app.recommendation.engine import get_filters, CATEGORY_ENGINES
from app.recommendation.questions import QUESTIONS

def test_all_categories_have_questions():
    for cat in ["mouse", "keyboard", "mousepad", "monitor", "microphone", "headphones"]:
        assert cat in QUESTIONS, f"No questions for {cat}"
        assert len(QUESTIONS[cat]) > 0

def test_mouse_gaming_filters():
    answers = {"use_case": "gaming", "wireless": "no", "budget": "mid"}
    filters = get_filters("mouse", answers)
    assert "price_max" in filters
    assert filters["price_max"] == 5000

def test_mouse_wireless_filter():
    answers = {"use_case": "work", "wireless": "yes", "budget": "high"}
    filters = get_filters("mouse", answers)
    assert filters.get("connection") == "Bluetooth"

def test_keyboard_compact_filter():
    answers = {"use_case": "gaming", "size": "compact", "switches": "tactile", "wireless": "no", "budget": "mid"}
    filters = get_filters("keyboard", answers)
    assert filters.get("form_factor") in ("TKL", "65%", "60%")

def test_monitor_gaming_refresh_rate():
    answers = {"use_case": "gaming", "size": "27", "budget": "mid"}
    filters = get_filters("monitor", answers)
    assert filters.get("refresh_rate_min", 0) >= 144
```

- [ ] **Step 2: Запустить тесты — убедиться что падают**

```powershell
pytest tests/test_recommendation.py -v
```

Ожидаемый вывод: `FAILED — ModuleNotFoundError`

- [ ] **Step 3: Создать recommendation/questions.py**

```python
QUESTIONS = {
    "mouse": [
        {
            "id": "use_case",
            "text": "Для чего будете использовать мышку?",
            "options": [
                {"value": "gaming", "label": "Игры"},
                {"value": "work",   "label": "Работа / офис"},
                {"value": "universal", "label": "Универсально"},
            ],
        },
        {
            "id": "wireless",
            "text": "Нужна беспроводная мышка?",
            "options": [
                {"value": "yes", "label": "Да, беспроводная"},
                {"value": "no",  "label": "Нет, проводная"},
                {"value": "any", "label": "Без разницы"},
            ],
        },
        {
            "id": "budget",
            "text": "Ваш бюджет?",
            "options": [
                {"value": "budget", "label": "До 2 000 ₽"},
                {"value": "mid",    "label": "2 000 – 5 000 ₽"},
                {"value": "high",   "label": "Свыше 5 000 ₽"},
            ],
        },
    ],
    "keyboard": [
        {
            "id": "use_case",
            "text": "Для чего нужна клавиатура?",
            "options": [
                {"value": "gaming",        "label": "Игры"},
                {"value": "typing",        "label": "Набор текста / офис"},
                {"value": "programming",   "label": "Программирование"},
            ],
        },
        {
            "id": "size",
            "text": "Важна ли компактность?",
            "options": [
                {"value": "full",    "label": "Нет, полноразмерная"},
                {"value": "compact", "label": "Да, компактная (TKL / 65% / 60%)"},
            ],
        },
        {
            "id": "switches",
            "text": "Какие переключатели предпочитаете?",
            "options": [
                {"value": "quiet",    "label": "Тихие (линейные)"},
                {"value": "tactile",  "label": "Тактильные"},
                {"value": "clicky",   "label": "С кликом"},
                {"value": "unknown",  "label": "Не знаю"},
            ],
        },
        {
            "id": "wireless",
            "text": "Нужна беспроводная клавиатура?",
            "options": [
                {"value": "yes", "label": "Да"},
                {"value": "no",  "label": "Нет"},
                {"value": "any", "label": "Без разницы"},
            ],
        },
        {
            "id": "budget",
            "text": "Ваш бюджет?",
            "options": [
                {"value": "budget", "label": "До 3 000 ₽"},
                {"value": "mid",    "label": "3 000 – 8 000 ₽"},
                {"value": "high",   "label": "Свыше 8 000 ₽"},
            ],
        },
    ],
    "mousepad": [
        {
            "id": "size",
            "text": "Какой размер коврика предпочитаете?",
            "options": [
                {"value": "S",  "label": "Маленький (S)"},
                {"value": "M",  "label": "Средний (M)"},
                {"value": "L",  "label": "Большой (L)"},
                {"value": "XL", "label": "Очень большой (XL)"},
            ],
        },
        {
            "id": "hardness",
            "text": "Какую поверхность предпочитаете?",
            "options": [
                {"value": "Soft", "label": "Мягкая (ткань)"},
                {"value": "Hard", "label": "Жёсткая (пластик)"},
                {"value": "any",  "label": "Без разницы"},
            ],
        },
        {
            "id": "rgb",
            "text": "Нужна ли RGB-подсветка?",
            "options": [
                {"value": "yes", "label": "Да"},
                {"value": "no",  "label": "Нет"},
            ],
        },
        {
            "id": "budget",
            "text": "Ваш бюджет?",
            "options": [
                {"value": "budget", "label": "До 1 000 ₽"},
                {"value": "mid",    "label": "1 000 – 3 000 ₽"},
                {"value": "high",   "label": "Свыше 3 000 ₽"},
            ],
        },
    ],
    "monitor": [
        {
            "id": "use_case",
            "text": "Для чего монитор?",
            "options": [
                {"value": "gaming",  "label": "Игры"},
                {"value": "work",    "label": "Работа / офис"},
                {"value": "design",  "label": "Дизайн / обработка фото"},
                {"value": "movies",  "label": "Кино / медиа"},
            ],
        },
        {
            "id": "size",
            "text": "Предпочтительный размер экрана?",
            "options": [
                {"value": "24", "label": "24\""},
                {"value": "27", "label": "27\""},
                {"value": "32", "label": "32\" и больше"},
            ],
        },
        {
            "id": "budget",
            "text": "Ваш бюджет?",
            "options": [
                {"value": "budget", "label": "До 15 000 ₽"},
                {"value": "mid",    "label": "15 000 – 35 000 ₽"},
                {"value": "high",   "label": "Свыше 35 000 ₽"},
            ],
        },
    ],
    "microphone": [
        {
            "id": "use_case",
            "text": "Для чего нужен микрофон?",
            "options": [
                {"value": "streaming",  "label": "Стриминг / подкасты"},
                {"value": "calls",      "label": "Звонки / онлайн-встречи"},
                {"value": "music",      "label": "Запись музыки"},
            ],
        },
        {
            "id": "connection",
            "text": "Тип подключения?",
            "options": [
                {"value": "USB", "label": "USB (plug & play)"},
                {"value": "XLR", "label": "XLR (студийный)"},
                {"value": "any", "label": "Без разницы"},
            ],
        },
        {
            "id": "budget",
            "text": "Ваш бюджет?",
            "options": [
                {"value": "budget", "label": "До 3 000 ₽"},
                {"value": "mid",    "label": "3 000 – 8 000 ₽"},
                {"value": "high",   "label": "Свыше 8 000 ₽"},
            ],
        },
    ],
    "headphones": [
        {
            "id": "use_case",
            "text": "Для чего нужны наушники?",
            "options": [
                {"value": "gaming", "label": "Игры"},
                {"value": "music",  "label": "Музыка"},
                {"value": "calls",  "label": "Звонки / работа"},
            ],
        },
        {
            "id": "type",
            "text": "Конструкция наушников?",
            "options": [
                {"value": "Over-ear", "label": "Полноразмерные (Over-ear)"},
                {"value": "On-ear",   "label": "Накладные (On-ear)"},
                {"value": "In-ear",   "label": "Вкладыши (In-ear)"},
            ],
        },
        {
            "id": "wireless",
            "text": "Нужны беспроводные?",
            "options": [
                {"value": "yes", "label": "Да"},
                {"value": "no",  "label": "Нет, проводные"},
                {"value": "any", "label": "Без разницы"},
            ],
        },
        {
            "id": "noise_cancellation",
            "text": "Нужно шумоподавление?",
            "options": [
                {"value": "Active",  "label": "Да, активное (ANC)"},
                {"value": "Passive", "label": "Пассивное (изоляция)"},
                {"value": "None",    "label": "Не нужно"},
            ],
        },
        {
            "id": "budget",
            "text": "Ваш бюджет?",
            "options": [
                {"value": "budget", "label": "До 3 000 ₽"},
                {"value": "mid",    "label": "3 000 – 10 000 ₽"},
                {"value": "high",   "label": "Свыше 10 000 ₽"},
            ],
        },
    ],
}
```

- [ ] **Step 4: Создать recommendation/engine.py**

```python
from typing import Dict, Any

MOUSE_BUDGET = {"budget": 2000, "mid": 5000, "high": 999999}
KEYBOARD_BUDGET = {"budget": 3000, "mid": 8000, "high": 999999}
MOUSEPAD_BUDGET = {"budget": 1000, "mid": 3000, "high": 999999}
MONITOR_BUDGET = {"budget": 15000, "mid": 35000, "high": 999999}
MICROPHONE_BUDGET = {"budget": 3000, "mid": 8000, "high": 999999}
HEADPHONES_BUDGET = {"budget": 3000, "mid": 10000, "high": 999999}

def _mouse_filters(answers: Dict[str, str]) -> Dict[str, Any]:
    f: Dict[str, Any] = {}
    f["price_max"] = MOUSE_BUDGET.get(answers.get("budget", "high"), 999999)
    wireless = answers.get("wireless")
    if wireless == "yes":
        f["connection"] = "Bluetooth"
    elif wireless == "no":
        f["connection"] = "USB"
    if answers.get("use_case") == "gaming":
        f["weight_max"] = 100
    return f

def _keyboard_filters(answers: Dict[str, str]) -> Dict[str, Any]:
    f: Dict[str, Any] = {}
    f["price_max"] = KEYBOARD_BUDGET.get(answers.get("budget", "high"), 999999)
    if answers.get("size") == "compact":
        f["form_factor"] = "TKL"
    switches = answers.get("switches")
    if switches == "quiet":
        f["switches"] = "Linear"
    elif switches == "tactile":
        f["switches"] = "Tactile"
    elif switches == "clicky":
        f["switches"] = "Clicky"
    wireless = answers.get("wireless")
    if wireless == "yes":
        f["connection"] = "Bluetooth"
    elif wireless == "no":
        f["connection"] = "USB"
    return f

def _mousepad_filters(answers: Dict[str, str]) -> Dict[str, Any]:
    f: Dict[str, Any] = {}
    f["price_max"] = MOUSEPAD_BUDGET.get(answers.get("budget", "high"), 999999)
    if answers.get("size") in ("S", "M", "L", "XL"):
        f["size"] = answers["size"]
    if answers.get("hardness") in ("Soft", "Hard"):
        f["hardness"] = answers["hardness"]
    if answers.get("rgb") == "yes":
        f["has_rgb"] = True
    elif answers.get("rgb") == "no":
        f["has_rgb"] = False
    return f

def _monitor_filters(answers: Dict[str, str]) -> Dict[str, Any]:
    f: Dict[str, Any] = {}
    f["price_max"] = MONITOR_BUDGET.get(answers.get("budget", "high"), 999999)
    use_case = answers.get("use_case")
    if use_case == "gaming":
        f["refresh_rate_min"] = 144
        f["matrix_type"] = "IPS"
    elif use_case == "design":
        f["matrix_type"] = "IPS"
    size = answers.get("size")
    if size:
        f["diagonal_min"] = float(size) - 1
        f["diagonal_max"] = float(size) + 2
    return f

def _microphone_filters(answers: Dict[str, str]) -> Dict[str, Any]:
    f: Dict[str, Any] = {}
    f["price_max"] = MICROPHONE_BUDGET.get(answers.get("budget", "high"), 999999)
    connection = answers.get("connection")
    if connection in ("USB", "XLR"):
        f["connection"] = connection
    use_case = answers.get("use_case")
    if use_case == "streaming":
        f["mic_type"] = "Condenser"
    elif use_case == "music":
        f["mic_type"] = "Condenser"
    return f

def _headphones_filters(answers: Dict[str, str]) -> Dict[str, Any]:
    f: Dict[str, Any] = {}
    f["price_max"] = HEADPHONES_BUDGET.get(answers.get("budget", "high"), 999999)
    h_type = answers.get("type")
    if h_type in ("Over-ear", "On-ear", "In-ear"):
        f["construction_type"] = h_type
    wireless = answers.get("wireless")
    if wireless == "yes":
        f["connection"] = "Wireless"
    elif wireless == "no":
        f["connection"] = "Wired"
    nc = answers.get("noise_cancellation")
    if nc in ("Active", "Passive", "None"):
        f["noise_cancellation"] = nc
    if answers.get("use_case") == "calls":
        f["has_microphone"] = True
    return f

CATEGORY_ENGINES = {
    "mouse":       _mouse_filters,
    "keyboard":    _keyboard_filters,
    "mousepad":    _mousepad_filters,
    "monitor":     _monitor_filters,
    "microphone":  _microphone_filters,
    "headphones":  _headphones_filters,
}

def get_filters(category: str, answers: Dict[str, str]) -> Dict[str, Any]:
    if category not in CATEGORY_ENGINES:
        raise ValueError(f"Unknown category: {category}")
    return CATEGORY_ENGINES[category](answers)
```

- [ ] **Step 5: Запустить тесты**

```powershell
pytest tests/test_recommendation.py -v
```

Ожидаемый вывод: `5 passed`

- [ ] **Step 6: Создать routers/recommendation.py**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.recommendation import RecommendationRequest, Question
from app.recommendation.questions import QUESTIONS
from app.recommendation.engine import get_filters
from app.models.mouse import Mouse
from app.models.keyboard import Keyboard
from app.models.mousepad import Mousepad
from app.models.monitor import Monitor
from app.models.microphone import Microphone
from app.models.headphones import Headphones

router = APIRouter(prefix="/recommend", tags=["recommendation"])

CATEGORY_MODELS = {
    "mouse":       Mouse,
    "keyboard":    Keyboard,
    "mousepad":    Mousepad,
    "monitor":     Monitor,
    "microphone":  Microphone,
    "headphones":  Headphones,
}

@router.get("/questions/{category}", response_model=List[Question])
def get_questions(category: str):
    from fastapi import HTTPException
    if category not in QUESTIONS:
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")
    return QUESTIONS[category]

@router.post("/")
def recommend(request: RecommendationRequest, db: Session = Depends(get_db)):
    from fastapi import HTTPException
    if request.category not in CATEGORY_MODELS:
        raise HTTPException(status_code=400, detail="Unknown category")

    filters = get_filters(request.category, request.answers)
    model = CATEGORY_MODELS[request.category]
    query = db.query(model)

    if "price_max" in filters:
        query = query.filter(model.price <= filters["price_max"])
    if "price_min" in filters:
        query = query.filter(model.price >= filters["price_min"])
    if "connection" in filters:
        query = query.filter(model.connection_types.contains(filters["connection"]))

    # Mouse-specific
    if hasattr(model, "weight_g") and "weight_max" in filters:
        query = query.filter(model.weight_g <= filters["weight_max"])

    # Keyboard-specific
    if hasattr(model, "form_factor") and "form_factor" in filters:
        query = query.filter(model.form_factor == filters["form_factor"])
    if hasattr(model, "switches") and "switches" in filters:
        query = query.filter(model.switches.contains(filters["switches"]))

    # Monitor-specific
    if hasattr(model, "refresh_rate_hz") and "refresh_rate_min" in filters:
        query = query.filter(model.refresh_rate_hz >= filters["refresh_rate_min"])
    if hasattr(model, "matrix_type") and "matrix_type" in filters:
        query = query.filter(model.matrix_type == filters["matrix_type"])
    if hasattr(model, "diagonal_inch") and "diagonal_min" in filters:
        query = query.filter(model.diagonal_inch >= filters["diagonal_min"])
    if hasattr(model, "diagonal_inch") and "diagonal_max" in filters:
        query = query.filter(model.diagonal_inch <= filters["diagonal_max"])

    # Mousepad-specific
    if hasattr(model, "size") and "size" in filters:
        query = query.filter(model.size == filters["size"])
    if hasattr(model, "hardness") and "hardness" in filters:
        query = query.filter(model.hardness == filters["hardness"])
    if hasattr(model, "has_rgb") and "has_rgb" in filters:
        query = query.filter(model.has_rgb == filters["has_rgb"])

    # Microphone-specific
    if hasattr(model, "mic_type") and "mic_type" in filters:
        query = query.filter(model.mic_type == filters["mic_type"])

    # Headphones-specific
    if hasattr(model, "construction_type") and "construction_type" in filters:
        query = query.filter(model.construction_type == filters["construction_type"])
    if hasattr(model, "noise_cancellation") and "noise_cancellation" in filters:
        query = query.filter(model.noise_cancellation == filters["noise_cancellation"])
    if hasattr(model, "has_microphone") and "has_microphone" in filters:
        query = query.filter(model.has_microphone == filters["has_microphone"])

    return query.limit(20).all()
```

- [ ] **Step 7: Добавить recommendation роутер в main.py**

В `app/main.py` добавить после существующих импортов роутеров:
```python
from app.routers import recommendation
```

И в блок `app.include_router(...)`:
```python
app.include_router(recommendation.router)
```

- [ ] **Step 8: Запустить все тесты**

```powershell
pytest tests/ -v
```

Ожидаемый вывод: все тесты проходят.

- [ ] **Step 9: Commit**

```powershell
git add app/recommendation/ app/routers/recommendation.py app/main.py tests/test_recommendation.py
git commit -m "feat: add questionnaire-based recommendation engine"
```

---

## Task 11: Store Locator API

**Files:**
- Create: `backend/app/routers/stores.py`

- [ ] **Step 1: Создать routers/stores.py**

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.parsers.dns_parser import DNSParser
from app.models.store_availability import StoreAvailability
from app.schemas.recommendation import StoreInfo

router = APIRouter(prefix="/stores", tags=["stores"])
dns_parser = DNSParser()

@router.get("/availability", response_model=List[StoreInfo])
def get_store_availability(
    product_type: str = Query(..., description="mouse/keyboard/..."),
    product_id: int = Query(..., description="ID товара в нашей БД"),
    city: str = Query(..., description="Название города"),
    db: Session = Depends(get_db),
):
    from fastapi import HTTPException
    from app.recommendation.engine import CATEGORY_ENGINES
    from app.models.mouse import Mouse
    from app.models.keyboard import Keyboard
    from app.models.mousepad import Mousepad
    from app.models.monitor import Monitor
    from app.models.microphone import Microphone
    from app.models.headphones import Headphones

    MODEL_MAP = {
        "mouse": Mouse, "keyboard": Keyboard, "mousepad": Mousepad,
        "monitor": Monitor, "microphone": Microphone, "headphones": Headphones,
    }

    if product_type not in MODEL_MAP:
        raise HTTPException(status_code=400, detail="Unknown product type")

    model = MODEL_MAP[product_type]
    product = db.query(model).filter(model.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if not product.dns_product_id:
        raise HTTPException(status_code=400, detail="Product has no DNS ID — store availability unavailable")

    # Сначала проверяем кэш в БД
    cached = (
        db.query(StoreAvailability)
        .filter(
            StoreAvailability.dns_product_id == product.dns_product_id,
            StoreAvailability.city == city,
        )
        .all()
    )
    if cached:
        return [StoreInfo(
            store_name=s.store_name or "DNS",
            store_address=s.store_address,
            city=s.city,
            in_stock=s.in_stock,
        ) for s in cached]

    # Парсим DNS
    stores = dns_parser.fetch_store_availability(product.dns_product_id, city)
    for s in stores:
        record = StoreAvailability(
            product_type=product_type,
            product_id=product_id,
            dns_product_id=product.dns_product_id,
            city=city,
            store_address=s["store_address"],
            store_name=s["store_name"],
            in_stock=s["in_stock"],
        )
        db.add(record)
    db.commit()

    return [StoreInfo(**s) for s in stores]
```

- [ ] **Step 2: Добавить stores роутер в main.py**

```python
from app.routers import stores
# ...
app.include_router(stores.router)
```

- [ ] **Step 3: Добавить миграцию для store_availability**

```powershell
alembic revision --autogenerate -m "add store availability table"
alembic upgrade head
```

- [ ] **Step 4: Запустить сервер и проверить все роуты в Swagger**

```powershell
uvicorn app.main:app --reload
```

Открыть `http://localhost:8000/docs` — проверить что все роуты присутствуют.

- [ ] **Step 5: Commit**

```powershell
git add app/routers/stores.py app/main.py alembic/
git commit -m "feat: add DNS store availability endpoint with city filter"
```

---

## Итог Plan 1

После выполнения всех задач у вас будет:

- ✅ PostgreSQL БД с таблицами для всех 6 категорий периферии
- ✅ FastAPI REST API с фильтрацией для каждой категории
- ✅ DNS парсер для получения товаров и наличия по городу
- ✅ Wildberries API клиент для обогащения каталога
- ✅ Планировщик автоматических обновлений данных (каждые 12 часов)
- ✅ Движок рекомендаций на основе опросника
- ✅ Эндпоинт поиска магазинов DNS по городу

**Следующий шаг: Plan 2 — React Frontend** (`2026-05-04-peripheral-dss-frontend.md`)

Запуск всех тестов перед переходом к фронтенду:
```powershell
pytest tests/ -v --tb=short
```
