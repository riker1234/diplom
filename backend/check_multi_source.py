"""
Show products that have links to more than one store.
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

def count_sources(item):
    return sum([
        bool(item.ozon_url),
        bool(getattr(item, 'wb_url', None)),
        bool(getattr(item, 'citilink_url', None)),
    ])

def main():
    db = SessionLocal()
    for model in MODELS:
        items = db.query(model).all()
        multi = [i for i in items if count_sources(i) >= 2]
        print(f"\n{model.__tablename__}: {len(multi)} товаров с 2+ источниками")
        for item in multi[:5]:
            sources = []
            if item.ozon_url: sources.append(f"Ozon {item.price or '?'}₽")
            if getattr(item, 'wb_url', None): sources.append(f"WB {item.wb_price or '?'}₽")
            if getattr(item, 'citilink_url', None): sources.append(f"Citilink {item.citilink_price or '?'}₽")
            print(f"  [{item.id}] {item.name[:50]}")
            print(f"       {' | '.join(sources)}")
    db.close()

if __name__ == "__main__":
    main()
