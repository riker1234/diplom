"""Refresh prices for EXISTING products by their stored source URLs.

The search-based parsers only touch the handful of products that appear in a
few search queries, so most of the catalog keeps stale prices. This walks
every product that has an ozon_url / citilink_url and re-fetches its CURRENT
price directly by URL.

Run from backend/ with DATABASE_URL pointing at the target DB:
    DATABASE_URL="<prod>" python refresh_prices.py citilink
    DATABASE_URL="<prod>" python refresh_prices.py ozon
    DATABASE_URL="<prod>" python refresh_prices.py ozon --limit 5   # quick test

Run the two sources sequentially (not in parallel) to avoid write contention.
"""
import re
import sys
import json
import time
import random

from app.database import SessionLocal
from app.models.mouse import Mouse
from app.models.keyboard import Keyboard
from app.models.monitor import Monitor
from app.models.headphones import Headphones
from app.models.microphone import Microphone
from app.models.mousepad import Mousepad
import app.parsers.ozon as OZ
import app.parsers.citilink as CT

_MODELS = [Mouse, Keyboard, Monitor, Headphones, Microphone, Mousepad]


def _parse_rub(s: str | None) -> float | None:
    if not s:
        return None
    digits = re.sub(r"[^\d]", "", s)
    return float(digits) if digits else None


def _ozon_price_by_url(url: str) -> tuple[str, float | None]:
    """Returns (status, price). status in {ok, oos, notfound}."""
    path = url.split("ozon.ru", 1)[-1] if "ozon.ru" in url else url
    data = OZ._browser_get(f"/api/entrypoint-api.bx/page/json/v2?url={path}")
    ws = (data or {}).get("widgetStates", {})
    for k, v in ws.items():
        if "webPrice" in k:
            try:
                obj = json.loads(v) if isinstance(v, str) else v
            except Exception:
                continue
            if obj.get("isAvailable") is False:
                return ("oos", None)
            price = _parse_rub(obj.get("cardPrice") or obj.get("price") or obj.get("originalPrice"))
            return ("ok", price)
    return ("notfound", None)


def refresh_ozon(db, limit: int | None = None) -> dict:
    updated = oos = failed = notfound = 0
    rows = []
    for model in _MODELS:
        rows += db.query(model).filter(model.ozon_url.isnot(None)).all()
    if limit:
        rows = rows[:limit]
    print(f"[ozon] товаров с ozon_url: {len(rows)}")
    for i, row in enumerate(rows, 1):
        try:
            status, price = _ozon_price_by_url(row.ozon_url)
            if status == "ok" and price and price >= 100:
                if row.price != price:
                    row.price = price
                updated += 1
            elif status == "oos":
                row.price = None
                oos += 1
            else:
                notfound += 1
            db.commit()
        except Exception as e:
            db.rollback()
            failed += 1
            print(f"[ozon] fail {row.ozon_url}: {e!r}")
        if i % 25 == 0:
            print(f"[ozon] {i}/{len(rows)}  upd={updated} oos={oos} nf={notfound} fail={failed}")
        time.sleep(random.uniform(0.4, 0.9))
    return {"updated": updated, "oos": oos, "notfound": notfound, "failed": failed}


def refresh_citilink(db, limit: int | None = None) -> dict:
    updated = oos = failed = 0
    rows = []
    for model in _MODELS:
        rows += db.query(model).filter(model.citilink_url.isnot(None)).all()
    if limit:
        rows = rows[:limit]
    print(f"[citilink] товаров с citilink_url: {len(rows)}")
    for i, row in enumerate(rows, 1):
        try:
            props, price = CT._get_properties(row.citilink_url)
            if props.pop("__oos__", False):
                row.citilink_price = None
                oos += 1
            elif price is not None:
                if row.citilink_price != price:
                    row.citilink_price = price
                updated += 1
            db.commit()
        except Exception as e:
            db.rollback()
            failed += 1
            print(f"[citilink] fail {row.citilink_url}: {e!r}")
        if i % 25 == 0:
            print(f"[citilink] {i}/{len(rows)}  upd={updated} oos={oos} fail={failed}")
        time.sleep(random.uniform(1.5, 3.0))
    return {"updated": updated, "oos": oos, "failed": failed}


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    source = sys.argv[1] if len(sys.argv) > 1 else "all"
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    db = SessionLocal()
    try:
        if source in ("ozon", "all"):
            print("=== refresh OZON ===")
            print(refresh_ozon(db, limit))
        if source in ("citilink", "all"):
            print("=== refresh CITILINK ===")
            print(refresh_citilink(db, limit))
    finally:
        db.close()
    print("Готово.")


if __name__ == "__main__":
    main()
