"""Точечный перепарс одного товара (кнопка «Обновить цену» в карточке).

Запускает собственный Playwright на время запроса: sync-API Playwright привязан
к потоку, а FastAPI обслуживает запросы из пула потоков, поэтому общий
браузер-синглтон здесь использовать нельзя. Глобальный замок сериализует
параллельные нажатия, чтобы не плодить несколько chromium одновременно.
"""
import json
import logging
import os
import re
import threading
from urllib.parse import unquote, urlsplit

from sqlalchemy import func

from app.parsers.browser import _STEALTH_JS, _UA

logger = logging.getLogger(__name__)

_refresh_lock = threading.Lock()

NAV_TIMEOUT_MS = 30_000

# План Б против гео-блокировок: российский прокси для запросов к маркетплейсам.
# Формат: http://user:pass@host:port (задаётся в переменных окружения Railway).
REFRESH_PROXY_URL = os.environ.get("REFRESH_PROXY_URL", "")


def _proxy_settings(url: str) -> dict | None:
    """Разбирает http://user:pass@host:port в формат Playwright.

    Chromium игнорирует логин/пароль, встроенные в URL, поэтому Playwright
    требует их отдельными полями username/password.
    """
    if not url:
        return None
    u = urlsplit(url)
    if not u.hostname:
        logger.warning("REFRESH_PROXY_URL задан, но не распарсился: %r", url)
        return None
    proxy: dict = {"server": f"{u.scheme or 'http'}://{u.hostname}:{u.port or 8080}"}
    if u.username:
        proxy["username"] = unquote(u.username)
    if u.password:
        proxy["password"] = unquote(u.password)
    return proxy


def _parse_rub(s: str | None) -> float | None:
    if not s:
        return None
    digits = re.sub(r"[^\d]", "", s)
    return float(digits) if digits else None


def _ozon_rating_from_ws(ws: dict) -> tuple[float | None, int | None]:
    """Рейтинг и число отзывов из виджета оценки на странице товара Ozon."""
    for k, v in ws.items():
        if "webSingleProductScore" in k:
            try:
                obj = json.loads(v) if isinstance(v, str) else v
            except Exception:
                continue
            text = obj.get("text") or ""  # например "4.8 • 1 608 отзывов"
            parts = text.split("•")
            rating = reviews = None
            m = re.search(r"\d+(?:[.,]\d+)?", parts[0]) if parts else None
            if m:
                rating = float(m.group().replace(",", "."))
            if len(parts) > 1:
                reviews = int(_parse_rub(parts[1]) or 0) or None
            return rating, reviews
    for k, v in ws.items():
        if "webReviewProductScore" in k:
            try:
                obj = json.loads(v) if isinstance(v, str) else v
            except Exception:
                continue
            rc = obj.get("reviewsCount")
            return None, (int(rc) if rc else None)
    return None, None


def _fetch_ozon(page, ozon_url: str) -> dict:
    """Цена/рейтинг товара через entrypoint-API Ozon (тот же путь, что в refresh_prices)."""
    path = ozon_url.split("ozon.ru", 1)[-1] if "ozon.ru" in ozon_url else ozon_url
    page.goto(
        f"https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2?url={path}",
        wait_until="load",
        timeout=NAV_TIMEOUT_MS,
    )
    body = page.inner_text("body")
    data = json.loads(body)  # антибот-страница не распарсится -> исключение -> "error"
    ws = data.get("widgetStates", {})

    status, price = "notfound", None
    for k, v in ws.items():
        if "webPrice" in k:
            try:
                obj = json.loads(v) if isinstance(v, str) else v
            except Exception:
                continue
            if obj.get("isAvailable") is False:
                status = "oos"
            else:
                status = "ok"
                price = _parse_rub(obj.get("cardPrice") or obj.get("price") or obj.get("originalPrice"))
            break
    rating, reviews = _ozon_rating_from_ws(ws)
    return {"status": status, "price": price, "rating": rating, "reviews": reviews}


def _fetch_citilink(page, citilink_url: str) -> dict:
    """Цена/наличие/рейтинг из JSON-LD на странице характеристик Ситилинка."""
    from app.parsers.citilink import _extract_jsonld

    page.goto(
        citilink_url.rstrip("/") + "/properties/",
        wait_until="load",
        timeout=NAV_TIMEOUT_MS,
    )
    ld = _extract_jsonld(page)
    if not ld:
        # Страница без JSON-LD = блокировка/смена вёрстки. Это ошибка чтения,
        # а НЕ «нет в наличии» — данные товара трогать нельзя.
        raise RuntimeError("citilink: JSON-LD not found (blocked or layout changed)")

    availability = (ld.get("availability") or "")
    if availability:
        in_stock = "InStock" in availability
    elif ld.get("price") is not None:
        in_stock = True
    else:
        raise RuntimeError("citilink: JSON-LD has neither availability nor price")

    return {
        "status": "ok" if in_stock else "oos",
        "price": ld.get("price"),
        "rating": ld.get("rating"),
        "reviews": ld.get("reviews"),
    }


def refresh_product(product, db) -> dict:
    """Перепарсивает товар по сохранённым URL источников и пишет в БД.

    Возвращает {"ozon": "ok|oos|notfound|error", "citilink": ...} — только
    для источников, у которых есть URL.
    """
    sources: dict[str, str] = {}
    touched = False

    with _refresh_lock:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as pw:
            launch_kwargs: dict = {
                "headless": True,
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            }
            proxy = _proxy_settings(REFRESH_PROXY_URL)
            if proxy:
                launch_kwargs["proxy"] = proxy
            browser = pw.chromium.launch(**launch_kwargs)
            try:
                ctx = browser.new_context(
                    user_agent=_UA,
                    locale="ru-RU",
                    viewport={"width": 1920, "height": 1080},
                )
                ctx.add_init_script(_STEALTH_JS)
                page = ctx.new_page()

                if getattr(product, "ozon_url", None):
                    try:
                        r = _fetch_ozon(page, product.ozon_url)
                        if r["status"] == "ok" and r["price"] and r["price"] >= 100:
                            product.price = r["price"]
                            touched = True
                        elif r["status"] == "oos":
                            product.price = None
                            touched = True
                        if r["rating"] is not None:
                            product.ozon_rating = r["rating"]
                            touched = True
                        if r["reviews"] is not None:
                            product.ozon_reviews = r["reviews"]
                            touched = True
                        sources["ozon"] = r["status"]
                    except Exception as e:
                        logger.warning("refresh ozon failed for %s: %r", product.ozon_url, e)
                        sources["ozon"] = "error"

                if getattr(product, "citilink_url", None):
                    try:
                        r = _fetch_citilink(page, product.citilink_url)
                        if r["status"] == "ok" and r["price"]:
                            product.citilink_price = r["price"]
                            touched = True
                        elif r["status"] == "oos":
                            product.citilink_price = None
                            touched = True
                        if r["rating"] is not None:
                            product.citilink_rating = r["rating"]
                            touched = True
                        if r["reviews"] is not None:
                            product.citilink_reviews = r["reviews"]
                            touched = True
                        sources["citilink"] = r["status"]
                    except Exception as e:
                        logger.warning("refresh citilink failed for %s: %r", product.citilink_url, e)
                        sources["citilink"] = "error"
            finally:
                browser.close()

    if touched or any(s in ("ok", "oos") for s in sources.values()):
        # Помечаем «проверено сейчас», даже если цена не изменилась
        product.updated_at = func.now()
    db.commit()
    return sources
