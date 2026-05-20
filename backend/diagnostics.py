"""
Full database and data quality diagnostics.
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models.mouse import Mouse
from app.models.keyboard import Keyboard
from app.models.monitor import Monitor
from app.models.headphones import Headphones
from app.models.microphone import Microphone
from app.models.mousepad import Mousepad

MODELS = [Mouse, Keyboard, Monitor, Headphones, Microphone, Mousepad]

issues = []

def warn(category, msg):
    issues.append(f"[{category}] {msg}")
    print(f"  ⚠  {msg}")


def check_table(db, model):
    name = model.__tablename__
    rows = db.query(model).all()
    print(f"\n── {name.upper()} ({len(rows)} записей) ──")

    no_name = [r for r in rows if not r.name]
    if no_name:
        warn(name, f"{len(no_name)} записей без name")

    no_price = [r for r in rows if r.price is None and getattr(r, 'wb_price', None) is None and getattr(r, 'citilink_price', None) is None]
    if no_price:
        warn(name, f"{len(no_price)} записей без цены ни на одном источнике")

    no_source = [r for r in rows if not r.ozon_url and not getattr(r, 'wb_url', None) and not getattr(r, 'citilink_url', None)]
    if no_source:
        warn(name, f"{len(no_source)} записей без ссылки ни на один источник")

    no_image = [r for r in rows if not r.image_url]
    pct = len(no_image) * 100 // len(rows) if rows else 0
    if pct > 20:
        warn(name, f"{len(no_image)} записей без фото ({pct}%)")
    else:
        print(f"  ✓  фото: {len(rows)-len(no_image)}/{len(rows)}")

    fake_brand = [r for r in rows if r.brand and re.match(r'^\d+(\.\d+)?$', r.brand.strip())]
    if fake_brand:
        warn(name, f"{len(fake_brand)} записей с рейтингом вместо бренда: {[r.brand for r in fake_brand[:3]]}")

    orig_brand = [r for r in rows if r.brand and r.brand.strip().lower() == 'оригинал']
    if orig_brand:
        warn(name, f"{len(orig_brand)} записей с брендом 'ОРИГИНАЛ'")

    # WB price mismatch
    wb_rows = [r for r in rows if r.price and getattr(r, 'wb_price', None)]
    mismatched = [r for r in wb_rows if max(r.price, r.wb_price) / min(r.price, r.wb_price) > 2.5]
    if mismatched:
        warn(name, f"{len(mismatched)} записей с подозрительной разницей Ozon/WB цены (>2.5x):")
        for r in mismatched[:3]:
            print(f"     id={r.id} ozon={r.price} wb={r.wb_price} '{r.name[:40]}'")

    # Duplicate names
    from collections import Counter
    name_counts = Counter(r.name for r in rows if r.name)
    dupes = [(n, c) for n, c in name_counts.items() if c > 1]
    if dupes:
        warn(name, f"{len(dupes)} дублирующихся названий:")
        for n, c in dupes[:3]:
            print(f"     x{c}: '{n[:50]}'")

    # Category-specific checks
    if name == 'mice':
        no_sensor = [r for r in rows if not r.sensor]
        if len(no_sensor) > len(rows) * 0.3:
            warn(name, f"{len(no_sensor)} мышей без сенсора ({len(no_sensor)*100//len(rows)}%)")
        no_conn = [r for r in rows if not r.connection_types]
        if no_conn:
            warn(name, f"{len(no_conn)} мышей без типа подключения")

    elif name == 'keyboards':
        no_sw = [r for r in rows if not r.switches]
        if len(no_sw) > len(rows) * 0.3:
            warn(name, f"{len(no_sw)} клавиатур без переключателей ({len(no_sw)*100//len(rows)}%)")

    elif name == 'monitors':
        no_matrix = [r for r in rows if not r.matrix_type]
        if no_matrix:
            warn(name, f"{len(no_matrix)} мониторов без типа матрицы")
        weird_hz = [r for r in rows if r.refresh_rate_hz and r.refresh_rate_hz not in (60,75,100,120,144,165,180,240,280,360)]
        if weird_hz:
            warn(name, f"{len(weird_hz)} мониторов с нестандартной частотой: {list(set(r.refresh_rate_hz for r in weird_hz))}")

    elif name == 'headphones':
        no_type = [r for r in rows if not r.construction_type]
        if no_type:
            warn(name, f"{len(no_type)} наушников без типа конструкции")

    elif name == 'microphones':
        no_mic_type = [r for r in rows if not r.mic_type]
        if no_mic_type:
            warn(name, f"{len(no_mic_type)} микрофонов без типа ({len(no_mic_type)*100//len(rows)}%)")

    elif name == 'mousepads':
        no_material = [r for r in rows if not r.surface_material]
        if no_material:
            warn(name, f"{len(no_material)} ковриков без материала поверхности")

    print(f"  ✓  источники: ozon={sum(1 for r in rows if r.ozon_url)}"
          f" wb={sum(1 for r in rows if getattr(r,'wb_url',None))}"
          f" citilink={sum(1 for r in rows if getattr(r,'citilink_url',None))}")


def main():
    db = SessionLocal()
    print("=" * 60)
    print("ДИАГНОСТИКА БАЗЫ ДАННЫХ")
    print("=" * 60)

    for model in MODELS:
        check_table(db, model)

    db.close()

    print("\n" + "=" * 60)
    print(f"ИТОГ: найдено {len(issues)} проблем")
    print("=" * 60)
    for i, issue in enumerate(issues, 1):
        print(f"{i:2}. {issue}")


if __name__ == "__main__":
    main()
