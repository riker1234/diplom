"""
Detach WB SKU/URL/price from product records where the price difference
between Ozon and WB is suspiciously large (> 2.5x), indicating a bad name match.
"""
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


def main():
    db = SessionLocal()
    total = 0

    for model in MODELS:
        rows = db.query(model).filter(
            model.wb_sku.isnot(None),
            model.price.isnot(None),
            model.wb_price.isnot(None),
        ).all()

        for item in rows:
            ratio = max(item.price, item.wb_price) / min(item.price, item.wb_price)
            if ratio > RATIO_THRESHOLD:
                print(f"  [{model.__tablename__}] id={item.id} price={item.price} wb={item.wb_price} "
                      f"ratio={ratio:.1f}x — detaching WB: {item.name[:50]}")
                item.wb_sku = None
                item.wb_url = None
                item.wb_price = None
                total += 1

    db.commit()
    db.close()
    print(f"\nDone. Detached WB from {total} records.")


if __name__ == "__main__":
    main()
