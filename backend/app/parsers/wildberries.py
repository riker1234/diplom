import re
import concurrent.futures
from playwright.sync_api import sync_playwright
from sqlalchemy.orm import Session
from app.models.mouse import Mouse

_WEIGHT_KEYS = {"вес", "масса"}
_CONNECTION_KEYS = {"тип подключения", "интерфейс"}
_SENSOR_KEYS = {"сенсор", "тип сенсора"}
_SWITCH_KEYS = {"переключатели", "микровыключатели"}


def _parse_weight(value: str) -> float | None:
    match = re.search(r"[\d]+[.,]?[\d]*", value)
    if match:
        return float(match.group().replace(",", "."))
    return None


def _map_mouse_characteristics(options: list[dict]) -> dict:
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
    vol = product_id // 100000
    part = product_id // 1000
    basket = _get_basket(vol)
    return f"https://basket-{basket}.wbbasket.ru/vol{vol}/part{part}/{product_id}/images/big/1.webp"


def _fetch_wb_data(query: str, limit: int = 100) -> tuple[list[dict], list[dict]]:
    """Открывает WB в headless-браузере, перехватывает API-ответы и получает детали."""
    products = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            locale="ru-RU",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/147.0.0.0 Safari/537.36"
            ),
        )
        page = context.new_page()

        # Перехватываем ответ поискового API
        def on_response(response):
            nonlocal products
            if "search.wb.ru" in response.url and response.status == 200:
                try:
                    data = response.json()
                    prods = data.get("data", {}).get("products", [])
                    if prods:
                        products = prods[:limit]
                except Exception:
                    pass

        page.on("response", on_response)

        # Открываем страницу поиска — браузер сам делает запросы с куками
        page.goto(
            f"https://www.wildberries.ru/catalog/0/search.aspx?search={query}",
            wait_until="domcontentloaded",
            timeout=30000,
        )
        page.wait_for_timeout(4000)

        details = []
        if products:
            ids = ";".join(str(p["id"]) for p in products[:50])
            detail_url = (
                f"https://card.wb.ru/cards/v1/detail"
                f"?appType=1&curr=rub&dest=-1257786&nm={ids}"
            )
            # Запрос через браузерный fetch — куки уже есть
            raw = page.evaluate(
                f"""async () => {{
                    const r = await fetch('{detail_url}');
                    return await r.json();
                }}"""
            )
            details = raw.get("data", {}).get("products", [])

        browser.close()

    return products, details


# Публичные функции оставляем для тестов
def _search_wb(query: str, limit: int = 100) -> list[dict]:
    products, _ = _fetch_wb_data(query, limit)
    return products


def _fetch_details(product_ids: list[int]) -> list[dict]:
    if not product_ids:
        return []
    ids = ";".join(str(i) for i in product_ids)
    detail_url = (
        f"https://card.wb.ru/cards/v1/detail"
        f"?appType=1&curr=rub&dest=-1257786&nm={ids}"
    )
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        raw = page.evaluate(
            f"""async () => {{
                const r = await fetch('{detail_url}');
                return await r.json();
            }}"""
        )
        browser.close()
    return raw.get("data", {}).get("products", [])


def parse_mice(db: Session) -> dict:
    added = updated = failed = 0

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_fetch_wb_data, "игровая мышь")
            products, details = future.result(timeout=60)
    except Exception as e:
        return {"added": 0, "updated": 0, "failed": 0, "error": str(e)}

    if not products:
        return {"added": 0, "updated": 0, "failed": 0}

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
