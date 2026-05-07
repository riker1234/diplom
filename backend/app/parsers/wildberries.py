import re
import requests
from sqlalchemy.orm import Session
from app.models.mouse import Mouse

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Ключи характеристик WB для каждого поля мыши
_WEIGHT_KEYS = {"вес", "масса"}
_CONNECTION_KEYS = {"тип подключения", "интерфейс"}
_SENSOR_KEYS = {"сенсор", "тип сенсора"}
_SWITCH_KEYS = {"переключатели", "микровыключатели"}


def _parse_weight(value: str) -> float | None:
    """Извлекает число из строки вида '95 г' или '95,5 г'."""
    match = re.search(r"[\d]+[.,]?[\d]*", value)
    if match:
        return float(match.group().replace(",", "."))
    return None


def _map_mouse_characteristics(options: list[dict]) -> dict:
    """Переводит список характеристик WB в поля модели Mouse."""
    result = {"weight_g": None, "connection_types": None, "sensor": None, "switches": None}
    for opt in options:
        name = opt.get("name", "").lower().strip()
        value = opt.get("value", "").strip()
        if name in _WEIGHT_KEYS:
            result["weight_g"] = _parse_weight(value)
        elif name in _CONNECTION_KEYS:
            result["connection_types"] = value
        elif name in _SENSOR_KEYS:
            result["sensor"] = value
        elif name in _SWITCH_KEYS:
            result["switches"] = value
    return result


def _get_basket(vol: int) -> str:
    """Определяет номер CDN-корзины WB по vol-части артикула."""
    thresholds = [
        143, 287, 431, 719, 1007, 1061, 1115, 1169, 1313, 1601,
        1655, 1919, 2045, 2189, 2405, 2621, 2837, 3053, 3269, 3485,
        3701, 3917, 4133, 4349,
    ]
    for i, t in enumerate(thresholds):
        if vol <= t:
            return str(i + 1).zfill(2)
    return "25"


def _build_image_url(product_id: int) -> str:
    """Строит URL главной картинки товара на CDN Wildberries."""
    vol = product_id // 100000
    part = product_id // 1000
    basket = _get_basket(vol)
    return f"https://basket-{basket}.wbbasket.ru/vol{vol}/part{part}/{product_id}/images/big/1.webp"


def _search_wb(query: str, limit: int = 100) -> list[dict]:
    """Ищет товары на WB по поисковому запросу."""
    url = "https://search.wb.ru/exactmatch/ru/common/v5/search"
    params = {"query": query, "resultset": "catalog", "limit": limit, "dest": "-1257786"}
    resp = requests.get(url, params=params, headers=_HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json().get("data", {}).get("products", [])


def _fetch_details(product_ids: list[int]) -> list[dict]:
    """Получает характеристики товаров по списку артикулов (до 100 за раз)."""
    url = "https://card.wb.ru/cards/v1/detail"
    params = {
        "appType": "1",
        "curr": "rub",
        "dest": "-1257786",
        "nm": ";".join(str(i) for i in product_ids),
    }
    resp = requests.get(url, params=params, headers=_HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json().get("data", {}).get("products", [])


def parse_mice(db: Session) -> dict:
    """Загружает мыши с WB и сохраняет в БД. Возвращает счётчики."""
    added = updated = failed = 0

    products = _search_wb("игровая мышь")
    if not products:
        return {"added": 0, "updated": 0, "failed": 0}

    product_ids = [p["id"] for p in products]
    details = _fetch_details(product_ids)
    details_map = {d["id"]: d for d in details}

    for product in products:
        try:
            pid = product["id"]
            options = details_map.get(pid, {}).get("options", [])
            chars = _map_mouse_characteristics(options)
            wb_sku = str(pid)
            price = product.get("priceU", 0) / 100

            existing = db.query(Mouse).filter(Mouse.wb_sku == wb_sku).first()
            if existing:
                existing.price = price
                existing.image_url = _build_image_url(pid)
                db.commit()
                updated += 1
            else:
                db.add(Mouse(
                    name=product.get("name", ""),
                    brand=product.get("brand", ""),
                    price=price,
                    wb_sku=wb_sku,
                    wb_url=f"https://www.wildberries.ru/catalog/{pid}/detail.aspx",
                    image_url=_build_image_url(pid),
                    **chars,
                ))
                db.commit()
                added += 1
        except Exception:
            failed += 1
            db.rollback()

    return {"added": added, "updated": updated, "failed": failed}
