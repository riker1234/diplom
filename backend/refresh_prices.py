"""Refresh prices for EXISTING products by their stored source URLs.

The search-based parsers only touch the handful of products that appear in a
few search queries, so most of the catalog keeps stale prices. This walks
every product that has an ozon_url / citilink_url and re-fetches its CURRENT
price directly by URL.

Resilient to transient drops of the remote DB connection (Railway proxy):
uses pool_pre_ping + per-product commit retry with session recreation, so a
network/DNS blip doesn't kill the whole run. Commits per product, so it is
safe to re-run.

Run from backend/ with DATABASE_URL pointing at the target DB:
    DATABASE_URL="<prod>" python refresh_prices.py citilink
    DATABASE_URL="<prod>" python refresh_prices.py ozon
    DATABASE_URL="<prod>" python refresh_prices.py ozon --limit 5   # quick test
"""
import re
import sys
import json
import time
import random

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.mouse import Mouse
from app.models.keyboard import Keyboard
from app.models.monitor import Monitor
from app.models.headphones import Headphones
from app.models.microphone import Microphone
from app.models.mousepad import Mousepad
import app.parsers.ozon as OZ
import app.parsers.citilink as CT

_MODELS = [Mouse, Keyboard, Monitor, Headphones, Microphone, Mousepad]


def _make_sessionmaker():
    url = settings.DATABASE_URL
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_engine(url, pool_pre_ping=True, pool_recycle=180)
    return sessionmaker(bind=engine)


_Session = _make_sessionmaker()


def _parse_rub(s: str | None) -> float | None:
    if not s:
        return None
    digits = re.sub(r"[^\d]", "", s)
    return float(digits) if digits else None


def _ozon_rating_from_ws(ws: dict) -> tuple[float | None, int | None]:
    """Rating + review count from the Ozon product-page score widget."""
    for k, v in ws.items():
        if "webSingleProductScore" in k:
            try:
                obj = json.loads(v) if isinstance(v, str) else v
            except Exception:
                continue
            text = obj.get("text") or ""  # e.g. "4.8 • 1 608 отзывов"
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


def _collect(url_attr: str) -> list[tuple]:
    """Read plain (model, id, url) tuples up front (avoids detached ORM rows)."""
    sess = _Session()
    rows = []
    try:
        for model in _MODELS:
            col = getattr(model, url_attr)
            for pid, url in sess.query(model.id, col).filter(col.isnot(None)).all():
                rows.append((model, pid, url))
    finally:
        sess.close()
    return rows


def _apply(model, pid: int, mutate) -> bool:
    """Open a fresh session, fetch row by id, run mutate(row), commit.
    Retries on transient DB errors with a new session. Returns True on success."""
    for attempt in range(3):
        sess = _Session()
        try:
            row = sess.get(model, pid)
            if row is None:
                return False
            mutate(row)
            sess.commit()
            return True
        except Exception as e:
            try:
                sess.rollback()
            except Exception:
                pass
            if attempt == 2:
                print(f"  DB fail id={pid}: {e!r}")
                return False
            time.sleep(3)
        finally:
            try:
                sess.close()
            except Exception:
                pass
    return False


def refresh_ozon(limit: int | None = None) -> dict:
    rows = _collect("ozon_url")
    if limit:
        rows = rows[:limit]
    print(f"[ozon] товаров с ozon_url: {len(rows)}")
    updated = oos = notfound = failed = 0
    for i, (model, pid, url) in enumerate(rows, 1):
        try:
            path = url.split("ozon.ru", 1)[-1] if "ozon.ru" in url else url
            data = OZ._browser_get(f"/api/entrypoint-api.bx/page/json/v2?url={path}")
            if data is None:
                # Сетевой сбой/антибот: ответа нет вообще — данные товара НЕ трогаем
                failed += 1
                print(f"  нет ответа (сеть/антибот): {url}")
                time.sleep(random.uniform(0.4, 0.9))
                continue

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

            def _mut(r, price=price, status=status, rating=rating, reviews=reviews):
                if status == "ok" and price and price >= 100:
                    r.price = price
                elif status in ("oos", "notfound"):
                    # oos: «нет в наличии»; notfound: Ozon ответил, но страницы
                    # товара больше нет (делистнут) — цена обнуляется, товар
                    # выпадает из подбора и комплекта
                    r.price = None
                if rating is not None:
                    r.ozon_rating = rating
                if reviews is not None:
                    r.ozon_reviews = reviews

            _apply(model, pid, _mut)
            if status == "ok" and price and price >= 100:
                updated += 1
            elif status == "oos":
                oos += 1
            else:
                notfound += 1
        except Exception as e:
            failed += 1
            print(f"  fetch fail {url}: {e!r}")
        if i % 25 == 0:
            print(f"[ozon] {i}/{len(rows)}  upd={updated} oos={oos} nf={notfound} fail={failed}")
        time.sleep(random.uniform(0.4, 0.9))
    return {"updated": updated, "oos": oos, "notfound": notfound, "failed": failed}


def refresh_citilink(limit: int | None = None) -> dict:
    rows = _collect("citilink_url")
    if limit:
        rows = rows[:limit]
    print(f"[citilink] товаров с citilink_url: {len(rows)}")
    updated = oos = failed = 0
    for i, (model, pid, url) in enumerate(rows, 1):
        try:
            props, price = CT._get_properties(url)
            is_oos = props.pop("__oos__", False)
            rating = props.get("__rating__")
            reviews = props.get("__reviews__")

            def _mut(r, is_oos=is_oos, price=price, rating=rating, reviews=reviews):
                if is_oos:
                    r.citilink_price = None
                elif price is not None:
                    r.citilink_price = price
                if rating is not None:
                    r.citilink_rating = rating
                if reviews is not None:
                    r.citilink_reviews = reviews

            _apply(model, pid, _mut)
            if is_oos:
                oos += 1
            elif price is not None:
                updated += 1
        except Exception as e:
            failed += 1
            print(f"  fetch fail {url}: {e!r}")
        if i % 25 == 0:
            print(f"[citilink] {i}/{len(rows)}  upd={updated} oos={oos} fail={failed}")
        time.sleep(random.uniform(1.5, 3.0))
    return {"updated": updated, "oos": oos, "failed": failed}


import urllib.request

_WB_UA = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept": "*/*",
    "Referer": "https://www.wildberries.ru/",
}


def _wb_detail(nm: int) -> dict | None:
    """Карточка товара WB по артикулу через card.wb.ru v4. None = снят с продажи."""
    url = (f"https://card.wb.ru/cards/v4/detail?appType=1&curr=rub"
           f"&dest=-1257786&spp=30&nm={nm}")
    req = urllib.request.Request(url, headers=_WB_UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.load(r)
    prods = (data.get("data") or {}).get("products") or data.get("products") or []
    return prods[0] if prods else None


def _wb_extract(p: dict) -> dict:
    """Цена/наличие/рейтинг/отзывы из карточки WB v4."""
    price = None
    qty = 0
    for s in (p.get("sizes") or []):
        pr = s.get("price") or {}
        v = pr.get("product") or pr.get("total") or pr.get("basic")
        if v and price is None:
            price = v / 100
        for st in (s.get("stocks") or []):
            qty += st.get("qty") or 0
    if qty == 0:
        qty = p.get("totalQuantity") or 0
    rating = p.get("reviewRating") or p.get("nmReviewRating") or p.get("rating") or None
    reviews = p.get("feedbacks") or p.get("nmFeedbacks") or None
    return {"price": price, "qty": qty, "rating": rating, "reviews": reviews}


def refresh_wb(limit: int | None = None) -> dict:
    rows = _collect("wb_sku")
    if limit:
        rows = rows[:limit]
    print(f"[wb] товаров с wb_sku: {len(rows)}")
    updated = oos = delisted = failed = 0
    for i, (model, pid, sku) in enumerate(rows, 1):
        try:
            nm = int(sku)
            p = _wb_detail(nm)
            if p is None:
                # снят с продажи — цена обнуляется, товар выпадает из подбора/комплекта
                _apply(model, pid, lambda r: setattr(r, "wb_price", None))
                delisted += 1
            else:
                d = _wb_extract(p)

                def _mut(r, d=d):
                    if d["qty"] and d["price"] and d["price"] >= 50:
                        r.wb_price = d["price"]
                    else:
                        r.wb_price = None  # нет в наличии
                    if d["rating"] is not None:
                        r.wb_rating = d["rating"]
                    if d["reviews"] is not None:
                        r.wb_reviews = d["reviews"]

                _apply(model, pid, _mut)
                if d["qty"] and d["price"]:
                    updated += 1
                else:
                    oos += 1
        except Exception as e:
            failed += 1
            print(f"  fetch fail wb_sku={sku}: {e!r}")
        if i % 50 == 0:
            print(f"[wb] {i}/{len(rows)}  upd={updated} oos={oos} delisted={delisted} fail={failed}")
        time.sleep(random.uniform(0.3, 0.7))
    return {"updated": updated, "oos": oos, "delisted": delisted, "failed": failed}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    source = sys.argv[1] if len(sys.argv) > 1 else "all"
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    if source in ("ozon", "all"):
        print("=== refresh OZON ===")
        print(refresh_ozon(limit))
    if source in ("citilink", "all"):
        print("=== refresh CITILINK ===")
        print(refresh_citilink(limit))
    if source in ("wb", "all"):
        print("=== refresh WB ===")
        print(refresh_wb(limit))
    print("Готово.")


if __name__ == "__main__":
    main()
