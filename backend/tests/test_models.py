from app.database import Base

def test_base_metadata_exists():
    assert Base.metadata is not None

def test_database_url_loaded():
    from app.config import settings
    assert settings.DATABASE_URL is not None
    assert "postgresql" in settings.DATABASE_URL or "sqlite" in settings.DATABASE_URL

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
