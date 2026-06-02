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
            ws = (data or {}).get("widgetStates", {})
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
            if status == "ok" and price and price >= 100:
                _apply(model, pid, lambda r: setattr(r, "price", price))
                updated += 1
            elif status == "oos":
                _apply(model, pid, lambda r: setattr(r, "price", None))
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
            if props.pop("__oos__", False):
                _apply(model, pid, lambda r: setattr(r, "citilink_price", None))
                oos += 1
            elif price is not None:
                _apply(model, pid, lambda r: setattr(r, "citilink_price", price))
                updated += 1
        except Exception as e:
            failed += 1
            print(f"  fetch fail {url}: {e!r}")
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

    if source in ("ozon", "all"):
        print("=== refresh OZON ===")
        print(refresh_ozon(limit))
    if source in ("citilink", "all"):
        print("=== refresh CITILINK ===")
        print(refresh_citilink(limit))
    print("Готово.")


if __name__ == "__main__":
    main()
