"""
Add test products to verify multi-source display in catalog.
Run once, then delete when no longer needed.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.mousepad import Mousepad

TEST_PRODUCTS = [
    # Один товар — три источника
    Mousepad(
        name="SteelSeries QcK Medium TEST",
        brand="SteelSeries",
        size="360x300",
        surface_material="Ткань",
        hardness="Control",
        has_rgb=False,
        thickness_mm=2.0,
        price=1490.0,          # Ozon
        ozon_sku="TEST-001",
        ozon_url="https://www.ozon.ru/product/test-001/",
        wb_price=1350.0,       # WB дешевле
        wb_sku="TEST-WB-001",
        wb_url="https://www.wildberries.ru/catalog/test-001/detail.aspx",
        citilink_price=1599.0, # Ситилинк дороже
        citilink_sku="TEST-CL-001",
        citilink_url="https://www.citilink.ru/product/test-001/",
        image_url="https://cdn1.ozone.ru/s3/multimedia-1/6197892893.jpg",
    ),
    # Только Ozon
    Mousepad(
        name="Razer Gigantus V2 TEST",
        brand="Razer",
        size="450x400",
        surface_material="Ткань",
        hardness="Control",
        has_rgb=False,
        thickness_mm=3.0,
        price=2290.0,
        ozon_sku="TEST-002",
        ozon_url="https://www.ozon.ru/product/test-002/",
        image_url="https://cdn1.ozone.ru/s3/multimedia-1/6197892893.jpg",
    ),
    # Только WB
    Mousepad(
        name="Logitech G440 TEST",
        brand="Logitech",
        size="340x280",
        surface_material="Пластик",
        hardness="Speed",
        has_rgb=False,
        thickness_mm=3.0,
        wb_price=3100.0,
        wb_sku="TEST-WB-003",
        wb_url="https://www.wildberries.ru/catalog/test-003/detail.aspx",
        image_url="https://cdn1.ozone.ru/s3/multimedia-1/6197892893.jpg",
    ),
    # Только Ситилинк
    Mousepad(
        name="HyperX Pulsefire Mat TEST",
        brand="HyperX",
        size="360x300",
        surface_material="Ткань",
        hardness="Control",
        has_rgb=False,
        thickness_mm=3.0,
        citilink_price=1890.0,
        citilink_sku="TEST-CL-004",
        citilink_url="https://www.citilink.ru/product/test-004/",
        image_url="https://cdn1.ozone.ru/s3/multimedia-1/6197892893.jpg",
    ),
]

def main():
    db = SessionLocal()
    added = 0
    for p in TEST_PRODUCTS:
        existing = db.query(Mousepad).filter(Mousepad.name == p.name).first()
        if existing:
            print(f"  skip (already exists): {p.name}")
            continue
        db.add(p)
        added += 1
        print(f"  added: {p.name}")
    db.commit()
    db.close()
    print(f"\nDone. Added {added} test products.")

if __name__ == "__main__":
    main()
