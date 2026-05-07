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
