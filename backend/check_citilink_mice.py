"""Просмотр мышей с Ситилинк в БД."""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'C:\Users\User\Desktop\diplom\backend')

from app.database import SessionLocal
from app.models.mouse import Mouse

db = SessionLocal()
mice = db.query(Mouse).filter(Mouse.citilink_sku != None).all()
print(f"Мышей с Ситилинк: {len(mice)}\n")
print(f"{'ID':>4}  {'Название':45}  {'Цена':>7}  {'DPI':>6}  {'Кнопок':>6}  {'Подкл.':20}  {'RGB':>4}  {'Источник'}")
print("-" * 120)
for m in mice:
    print(
        f"{m.id:>4}  {(m.name or '')[:45]:45}  "
        f"{m.citilink_price or 0:>7.0f}  "
        f"{m.max_dpi or 0:>6}  "
        f"{m.button_count or 0:>6}  "
        f"{(m.connection_types or '')[:20]:20}  "
        f"{'да' if m.has_rgb else 'нет':>4}  "
        f"{m.source}"
    )
db.close()
