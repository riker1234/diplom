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


def test_parse_mice_requires_admin_key():
    response = client.post("/admin/parse/mice")
    assert response.status_code == 422


def test_parse_mice_rejects_wrong_key():
    response = client.post("/admin/parse/mice", headers={"X-Admin-Key": "wrong"})
    assert response.status_code == 403


def test_parse_mice_accepts_correct_key():
    with patch("app.routers.admin.parse_mice", return_value=_FAKE_RESULT):
        response = client.post("/admin/parse/mice", headers={"X-Admin-Key": "diplom2026"})
    assert response.status_code == 200
    assert response.json() == _FAKE_RESULT
