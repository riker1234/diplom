import os
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

from unittest.mock import patch
from app.config import settings
from app.parsers.wildberries import (
    _parse_float,
    _parse_int,
    _parse_bool,
    _map_mouse,
    _map_keyboard,
    _map_monitor,
    _map_headphones,
    _map_microphone,
    _map_mousepad,
    _build_image_url,
    _fetch_details,
    _search_wb,
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

def test_map_mouse_weight():
    result = _map_mouse([{"name": "Вес", "value": "70 г"}])
    assert result["weight_g"] == 70.0

def test_map_mouse_connection_types():
    result = _map_mouse([{"name": "Тип подключения", "value": "USB"}])
    assert result["connection_types"] == "USB"

def test_map_mouse_sensor():
    result = _map_mouse([{"name": "Сенсор", "value": "PixArt 3212"}])
    assert result["sensor"] == "PixArt 3212"

def test_map_mouse_switches():
    result = _map_mouse([{"name": "Переключатели", "value": "Omron"}])
    assert result["switches"] == "Omron"

def test_map_mouse_unknown_field_returns_none():
    result = _map_mouse([{"name": "Цвет", "value": "Чёрный"}])
    assert result == {"weight_g": None, "connection_types": None, "sensor": None, "switches": None}

def test_map_mouse_empty_options():
    result = _map_mouse([])
    assert result == {"weight_g": None, "connection_types": None, "sensor": None, "switches": None}


# ── Маппер клавиатуры ─────────────────────────────────────────────────────────

def test_map_keyboard_switches():
    result = _map_keyboard([{"name": "Переключатели", "value": "Cherry MX Red"}])
    assert result["switches"] == "Cherry MX Red"

def test_map_keyboard_form_factor():
    result = _map_keyboard([{"name": "Форм-фактор", "value": "TKL"}])
    assert result["form_factor"] == "TKL"

def test_map_keyboard_connection_types():
    result = _map_keyboard([{"name": "Тип подключения", "value": "USB, Bluetooth"}])
    assert result["connection_types"] == "USB, Bluetooth"

def test_map_keyboard_empty():
    result = _map_keyboard([])
    assert all(v is None for v in result.values())


# ── Маппер монитора ───────────────────────────────────────────────────────────

def test_map_monitor_refresh_rate():
    result = _map_monitor([{"name": "Частота обновления", "value": "144 Гц"}])
    assert result["refresh_rate_hz"] == 144

def test_map_monitor_diagonal():
    result = _map_monitor([{"name": "Диагональ", "value": "27\""}])
    assert result["diagonal_inch"] == 27.0

def test_map_monitor_matrix_type():
    result = _map_monitor([{"name": "Тип матрицы", "value": "IPS"}])
    assert result["matrix_type"] == "IPS"

def test_map_monitor_resolution():
    result = _map_monitor([{"name": "Разрешение", "value": "1920x1080"}])
    assert result["resolution"] == "1920x1080"


# ── Маппер наушников ──────────────────────────────────────────────────────────

def test_map_headphones_has_microphone_yes():
    result = _map_headphones([{"name": "Микрофон", "value": "Да"}])
    assert result["has_microphone"] is True

def test_map_headphones_has_microphone_no():
    result = _map_headphones([{"name": "Микрофон", "value": "Нет"}])
    assert result["has_microphone"] is False

def test_map_headphones_connection():
    result = _map_headphones([{"name": "Тип подключения", "value": "Bluetooth"}])
    assert result["connection_types"] == "Bluetooth"

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

def test_map_microphone_frequency():
    result = _map_microphone([{"name": "Диапазон частот", "value": "20-20000 Гц"}])
    assert result["frequency_range"] == "20-20000 Гц"


# ── Маппер коврика ────────────────────────────────────────────────────────────

def test_map_mousepad_has_rgb_yes():
    result = _map_mousepad([{"name": "Подсветка", "value": "Да"}])
    assert result["has_rgb"] is True

def test_map_mousepad_has_rgb_no():
    result = _map_mousepad([{"name": "Подсветка", "value": "Нет"}])
    assert result["has_rgb"] is False

def test_map_mousepad_hardness():
    result = _map_mousepad([{"name": "Жёсткость", "value": "мягкий"}])
    assert result["hardness"] == "мягкий"

def test_map_mousepad_size():
    result = _map_mousepad([{"name": "Размер", "value": "450x400 мм"}])
    assert result["size"] == "450x400 мм"

def test_map_mousepad_no_rgb_defaults_false():
    result = _map_mousepad([])
    assert result["has_rgb"] is False


# ── Построитель URL изображения ───────────────────────────────────────────────

def test_build_image_url_contains_product_id():
    url = _build_image_url(12345678)
    assert "12345678" in url
    assert url.startswith("https://basket-")
    assert url.endswith("1.webp")


# ── _fetch_details ─────────────────────────────────────────────────────────────

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


def test_fetch_details_returns_dict_keyed_by_id():
    with patch("app.parsers.wildberries.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = _FAKE_DETAIL_RESPONSE
        result = _fetch_details([12345678])
    assert 12345678 in result
    assert isinstance(result[12345678], list)
    assert len(result[12345678]) == 2


def test_fetch_details_empty_on_http_error():
    with patch("app.parsers.wildberries.requests.get") as mock_get:
        mock_get.return_value.status_code = 429
        result = _fetch_details([12345678])
    assert result == {}


# ── parse_mice (интеграция с БД) ──────────────────────────────────────────────

_FAKE_PRODUCTS = [
    {
        "id": 12345678,
        "name": "Игровая мышь Test",
        "brand": "TestBrand",
        "sizes": [{"price": {"product": 199000}}],
    }
]

_FAKE_DETAILS_DICT = {
    12345678: [
        {"name": "Вес", "value": "70 г"},
        {"name": "Тип подключения", "value": "USB"},
    ]
}


def test_parse_mice_adds_new_product(db):
    with patch("app.parsers.wildberries._fetch_all", return_value=(_FAKE_PRODUCTS, _FAKE_DETAILS_DICT)):
        result = parse_mice(db)
    assert result["added"] == 1
    assert result["updated"] == 0
    assert result["failed"] == 0
    mouse = db.query(Mouse).filter(Mouse.wb_sku == "12345678").first()
    assert mouse is not None
    assert mouse.weight_g == 70.0
    assert mouse.connection_types == "USB"
    assert mouse.price == 1990.0


def test_parse_mice_updates_existing_product(db):
    existing = Mouse(name="Old Name", price=1000.0, wb_sku="99999999")
    db.add(existing)
    db.commit()
    updated_products = [
        {"id": 99999999, "name": "New Name", "brand": "Brand", "sizes": [{"price": {"product": 250000}}]}
    ]
    with patch("app.parsers.wildberries._fetch_all", return_value=(updated_products, {})):
        result = parse_mice(db)
    assert result["updated"] == 1
    assert result["added"] == 0
    mouse = db.query(Mouse).filter(Mouse.wb_sku == "99999999").first()
    assert mouse.price == 2500.0


def test_parse_mice_returns_error_on_exception(db):
    with patch("app.parsers.wildberries._fetch_all", side_effect=RuntimeError("timeout")):
        result = parse_mice(db)
    assert "error" in result
    assert result["added"] == 0
