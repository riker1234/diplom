"""
Backfill image_url for WB products that have wb_sku but no image_url.
Uses the deterministic basket URL formula — no HTTP requests needed.
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


def _get_basket(vol: int) -> str:
    ranges = [
        (143, "01"), (287, "02"), (431, "03"), (719, "04"),
        (1007, "05"), (1061, "06"), (1115, "07"), (1169, "08"),
        (1313, "09"), (1601, "10"), (1655, "11"), (1919, "12"),
        (2045, "13"), (2189, "14"), (2405, "15"), (2621, "16"),
        (2837, "17"), (3053, "18"), (3269, "19"), (3485, "20"),
        (3701, "21"), (3917, "22"), (4133, "23"), (4349, "24"),
    ]
    for max_vol, basket in ranges:
        if vol <= max_vol:
            return basket
    return "25"


def make_wb_image_url(wb_sku: str) -> str | None:
    try:
        pid = int(wb_sku)
        vol = pid // 100000
        part = pid // 1000
        basket = _get_basket(vol)
        return f"https://basket-{basket}.wbbasket.ru/vol{vol}/part{part}/{pid}/images/big/1.webp"
    except Exception:
        return None


def main():
    db = SessionLocal()
    total = 0

    for model in MODELS:
        candidates = (
            db.query(model)
            .filter(model.wb_sku.isnot(None), model.image_url.is_(None))
            .all()
        )
        print(f"{model.__tablename__}: {len(candidates)} without image")
        for item in candidates:
            url = make_wb_image_url(item.wb_sku)
            if url:
                item.image_url = url
                total += 1

    db.commit()
    db.close()
    print(f"\nDone. Updated {total} records.")


if __name__ == "__main__":
    main()
