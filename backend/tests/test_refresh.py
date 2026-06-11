"""Тесты эндпоинта POST /refresh/{category}/{id} (сервис парсинга мокается)."""
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.mouse import Mouse
from app.routers import refresh as refresh_router

_engine = create_engine(
    "sqlite:///./test_refresh.db", connect_args={"check_same_thread": False}
)
_Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
Base.metadata.create_all(bind=_engine)


def _override_get_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client():
    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    if previous is not None:
        app.dependency_overrides[get_db] = previous
    else:
        app.dependency_overrides.pop(get_db, None)


def _make_mouse(**kw) -> int:
    db = _Session()
    try:
        m = Mouse(name=kw.pop("name", "Test Mouse"), **kw)
        db.add(m)
        db.commit()
        return m.id
    finally:
        db.close()


def test_refresh_unknown_category_404(client):
    assert client.post("/refresh/printer/1").status_code == 404


def test_refresh_missing_product_404(client):
    assert client.post("/refresh/mouse/999999").status_code == 404


def test_refresh_fresh_product_is_throttled(client, monkeypatch):
    def boom(product, db):
        raise AssertionError("service must not be called for fresh products")

    monkeypatch.setattr(refresh_router.refresh_service, "refresh_product", boom)
    pid = _make_mouse(ozon_url="https://ozon.ru/product/x", updated_at=datetime.utcnow())

    resp = client.post(f"/refresh/mouse/{pid}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["refreshed"] is False
    assert "актуальна" in data["message"]


def test_refresh_without_sources(client, monkeypatch):
    def boom(product, db):
        raise AssertionError("service must not be called without source urls")

    monkeypatch.setattr(refresh_router.refresh_service, "refresh_product", boom)
    pid = _make_mouse(updated_at=datetime.utcnow() - timedelta(hours=5))

    data = client.post(f"/refresh/mouse/{pid}").json()
    assert data["refreshed"] is False
    assert "источник" in data["message"].lower()


def test_refresh_stale_product_updates_price(client, monkeypatch):
    def fake_refresh(product, db):
        product.price = 999.0
        product.ozon_rating = 4.9
        db.commit()
        return {"ozon": "ok"}

    monkeypatch.setattr(refresh_router.refresh_service, "refresh_product", fake_refresh)
    pid = _make_mouse(
        ozon_url="https://ozon.ru/product/x",
        price=1234.0,
        updated_at=datetime.utcnow() - timedelta(hours=5),
    )

    data = client.post(f"/refresh/mouse/{pid}").json()
    assert data["refreshed"] is True
    assert data["sources"] == {"ozon": "ok"}
    assert data["updated"]["price"] == 999.0
    assert data["updated"]["ozon_rating"] == 4.9


def test_refresh_all_sources_failed(client, monkeypatch):
    def fake_refresh(product, db):
        return {"ozon": "error"}

    monkeypatch.setattr(refresh_router.refresh_service, "refresh_product", fake_refresh)
    pid = _make_mouse(
        ozon_url="https://ozon.ru/product/x",
        price=1234.0,
        updated_at=datetime.utcnow() - timedelta(hours=5),
    )

    data = client.post(f"/refresh/mouse/{pid}").json()
    assert data["refreshed"] is False
    assert data["updated"]["price"] == 1234.0


def test_proxy_settings_parsing():
    from app.services.refresh import _proxy_settings

    assert _proxy_settings("") is None
    p = _proxy_settings("http://user123:pa55@193.124.55.10:8000")
    assert p == {"server": "http://193.124.55.10:8000", "username": "user123", "password": "pa55"}
    # без авторизации
    assert _proxy_settings("http://10.0.0.1:3128") == {"server": "http://10.0.0.1:3128"}
