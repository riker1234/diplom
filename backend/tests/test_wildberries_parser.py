from app.config import settings


def test_admin_key_is_set():
    assert settings.ADMIN_KEY is not None
    assert len(settings.ADMIN_KEY) > 0


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


# ── Тесты API-клиента и parse_mice ───────────────────────────────────────────

from unittest.mock import patch, MagicMock
from app.parsers.wildberries import _search_wb, _fetch_details, parse_mice
from app.models.mouse import Mouse

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
