import os
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_admin.db")

from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

_ENGINE = create_engine("sqlite:///./test_admin.db", connect_args={"check_same_thread": False})
Base.metadata.create_all(bind=_ENGINE)
_Session = sessionmaker(bind=_ENGINE)


def _override_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_db
client = TestClient(app)

_FAKE_RESULT = {"added": 5, "updated": 2, "failed": 0}
_ADMIN_HEADER = {"X-Admin-Key": "diplom2026"}
_WRONG_HEADER = {"X-Admin-Key": "wrong"}

# ── Авторизация (общая для всех эндпоинтов) ───────────────────────────────────

def test_parse_mice_requires_admin_key():
    assert client.post("/admin/parse/mice").status_code == 422

def test_parse_mice_rejects_wrong_key():
    assert client.post("/admin/parse/mice", headers=_WRONG_HEADER).status_code == 403

def test_parse_keyboards_rejects_wrong_key():
    assert client.post("/admin/parse/keyboards", headers=_WRONG_HEADER).status_code == 403

def test_parse_monitors_rejects_wrong_key():
    assert client.post("/admin/parse/monitors", headers=_WRONG_HEADER).status_code == 403

def test_parse_headphones_rejects_wrong_key():
    assert client.post("/admin/parse/headphones", headers=_WRONG_HEADER).status_code == 403

def test_parse_microphones_rejects_wrong_key():
    assert client.post("/admin/parse/microphones", headers=_WRONG_HEADER).status_code == 403

def test_parse_mousepads_rejects_wrong_key():
    assert client.post("/admin/parse/mousepads", headers=_WRONG_HEADER).status_code == 403


# ── Успешный запуск (с моком парсера) ─────────────────────────────────────────

def test_parse_mice_accepts_correct_key():
    with patch("app.routers.admin.parse_mice", return_value=_FAKE_RESULT):
        response = client.post("/admin/parse/mice", headers=_ADMIN_HEADER)
    assert response.status_code == 200
    assert response.json() == _FAKE_RESULT

def test_parse_keyboards_accepts_correct_key():
    with patch("app.routers.admin.parse_keyboards", return_value=_FAKE_RESULT):
        response = client.post("/admin/parse/keyboards", headers=_ADMIN_HEADER)
    assert response.status_code == 200
    assert response.json() == _FAKE_RESULT

def test_parse_monitors_accepts_correct_key():
    with patch("app.routers.admin.parse_monitors", return_value=_FAKE_RESULT):
        response = client.post("/admin/parse/monitors", headers=_ADMIN_HEADER)
    assert response.status_code == 200
    assert response.json() == _FAKE_RESULT

def test_parse_headphones_accepts_correct_key():
    with patch("app.routers.admin.parse_headphones", return_value=_FAKE_RESULT):
        response = client.post("/admin/parse/headphones", headers=_ADMIN_HEADER)
    assert response.status_code == 200
    assert response.json() == _FAKE_RESULT

def test_parse_microphones_accepts_correct_key():
    with patch("app.routers.admin.parse_microphones", return_value=_FAKE_RESULT):
        response = client.post("/admin/parse/microphones", headers=_ADMIN_HEADER)
    assert response.status_code == 200
    assert response.json() == _FAKE_RESULT

def test_parse_mousepads_accepts_correct_key():
    with patch("app.routers.admin.parse_mousepads", return_value=_FAKE_RESULT):
        response = client.post("/admin/parse/mousepads", headers=_ADMIN_HEADER)
    assert response.status_code == 200
    assert response.json() == _FAKE_RESULT
