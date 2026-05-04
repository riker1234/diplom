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
