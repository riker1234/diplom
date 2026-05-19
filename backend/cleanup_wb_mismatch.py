"""
1. Detach WB from products where Ozon/WB price ratio > 2.5x (different products).
2. Fix brand field: clear values that are ratings like "4.9", "5.0".
3. Detach WB from products with generic short name and no real brand.
"""
import re
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.mouse import Mouse
from app.models.keyboard import Keyboard
from app.models.monitor import Monitor
from app.models.headphones import Headphones
from app.models.microphone import Microphone
from app.models.mousepad import Mousepad

MODELS = [Mouse, Keyboard, Monitor, Headphones, Microphone, Mousepad]
RATIO_THRESHOLD = 2.5


def is_rating(value: str) -> bool:
    return bool(re.match(r"^\d+(\.\d+)?$", (value or "").strip()))


def is_generic_name(name: str, brand: str) -> bool:
    return not brand and len((name or "").strip()) < 30


def main():
    db = SessionLocal()
    detached = 0
    brand_fixed = 0

    for model in MODELS:
        rows = db.query(model).all()

        for item in rows:
            # Fix brand: clear ratings stored as brand
            if item.brand and is_rating(item.brand):
                print(f"  [{model.__tablename__}] id={item.id} clear brand '{item.brand}': {item.name[:50]}")
                item.brand = None
                brand_fixed += 1

        # Detach WB where price ratio is too large
        wb_rows = db.query(model).filter(
            model.wb_sku.isnot(None),
            model.price.isnot(None),
            model.wb_price.isnot(None),
        ).all()

        for item in wb_rows:
            ratio = max(item.price, item.wb_price) / min(item.price, item.wb_price)
            if ratio > RATIO_THRESHOLD:
                print(f"  [{model.__tablename__}] id={item.id} price={item.price} wb={item.wb_price} "
                      f"ratio={ratio:.1f}x — detaching WB: {item.name[:50]}")
                item.wb_sku = None
                item.wb_url = None
                item.wb_price = None
                detached += 1
                continue

            # Detach WB from generic nameless products (no real brand, short name)
            if item.wb_sku and is_generic_name(item.name, item.brand):
                print(f"  [{model.__tablename__}] id={item.id} generic name — detaching WB: {item.name[:50]}")
                item.wb_sku = None
                item.wb_url = None
                item.wb_price = None
                detached += 1

    db.commit()
    db.close()
    print(f"\nDone. Brands fixed: {brand_fixed}. WB detached: {detached}.")


if __name__ == "__main__":
    main()
