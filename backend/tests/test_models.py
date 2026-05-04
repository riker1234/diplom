from app.database import Base

def test_base_metadata_exists():
    assert Base.metadata is not None

def test_database_url_loaded():
    from app.config import settings
    assert settings.DATABASE_URL is not None
    assert "postgresql" in settings.DATABASE_URL or "sqlite" in settings.DATABASE_URL
