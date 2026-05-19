"""
Backfill / fix image_url for WB products.
- Products with no image_url: generate from formula
- Products with 404 image_url: try baskets 25-42 to find the right one
"""
import sys, os, time, random
sys.path.insert(0, os.path.dirname(__file__))

import requests
from app.database import SessionLocal
from app.models.mouse import Mouse
from app.models.keyboard import Keyboard
from app.models.monitor import Monitor
from app.models.headphones import Headphones
from app.models.microphone import Microphone
from app.models.mousepad import Mousepad

MODELS = [Mouse, Keyboard, Monitor, Headphones, Microphone, Mousepad]

HEADERS = {"User-Agent": "Mozilla/5.0"}


def _get_basket(vol: int) -> str:
    ranges = [
        (143, "01"), (287, "02"), (431, "03"), (719, "04"),
        (1007, "05"), (1061, "06"), (1115, "07"), (1169, "08"),
        (1313, "09"), (1601, "10"), (1655, "11"), (1919, "12"),
        (2045, "13"), (2189, "14"), (2405, "15"), (2621, "16"),
        (2837, "17"), (3053, "18"), (3269, "19"), (3485, "20"),
        (3701, "21"), (3917, "22"), (4133, "23"), (4349, "24"),
        (4565, "25"), (4781, "26"), (4997, "27"), (5213, "28"),
        (5429, "29"), (5645, "30"), (5861, "31"), (6077, "32"),
        (6293, "33"), (6851, "34"), (7407, "35"), (7963, "36"),
        (8519, "37"), (9075, "38"), (9631, "39"),
    ]
    for max_vol, basket in ranges:
        if vol <= max_vol:
            return basket
    return "40"


def make_wb_image_url(wb_sku: str, basket: str | None = None) -> str | None:
    try:
        pid = int(wb_sku)
        vol = pid // 100000
        part = pid // 1000
        b = basket or _get_basket(vol)
        return f"https://basket-{b}.wbbasket.ru/vol{vol}/part{part}/{pid}/images/big/1.webp"
    except Exception:
        return None


def find_working_url(wb_sku: str) -> str | None:
    """Try formula first, then brute-force baskets 25-42."""
    url = make_wb_image_url(wb_sku)
    if url:
        try:
            if requests.head(url, headers=HEADERS, timeout=8).status_code == 200:
                return url
        except Exception:
            pass
    # Try other baskets
    pid = int(wb_sku)
    vol = pid // 100000
    part = pid // 1000
    for b in range(25, 43):
        basket = str(b).zfill(2)
        candidate = f"https://basket-{basket}.wbbasket.ru/vol{vol}/part{part}/{pid}/images/big/1.webp"
        try:
            if requests.head(candidate, headers=HEADERS, timeout=5).status_code == 200:
                return candidate
        except Exception:
            pass
        time.sleep(0.1)
    return None


def is_broken(url: str) -> bool:
    try:
        return requests.head(url, headers=HEADERS, timeout=8).status_code != 200
    except Exception:
        return True


def main():
    db = SessionLocal()
    total = 0

    for model in MODELS:
        # Products with no image at all
        no_img = db.query(model).filter(
            model.wb_sku.isnot(None), model.image_url.is_(None)
        ).all()
        # Products with WB image URL that might be broken
        has_wb_img = db.query(model).filter(
            model.wb_sku.isnot(None),
            model.image_url.ilike("%wbbasket%"),
        ).all()

        candidates = no_img + has_wb_img
        print(f"\n{model.__tablename__}: {len(no_img)} no image, {len(has_wb_img)} WB urls to verify")

        for item in candidates:
            needs_fix = item.image_url is None or is_broken(item.image_url)
            if not needs_fix:
                continue
            print(f"  fixing [{item.wb_sku}] {item.name[:40]}")
            url = find_working_url(item.wb_sku)
            if url:
                item.image_url = url
                db.commit()
                total += 1
                print(f"    ✓ {url}")
            else:
                print(f"    - no image found")
            time.sleep(random.uniform(0.2, 0.5))

    db.close()
    print(f"\nDone. Fixed {total} records.")


if __name__ == "__main__":
    main()
