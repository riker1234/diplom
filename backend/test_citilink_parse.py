"""Просмотр мышей с Ситилинк в БД."""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'C:\Users\User\Desktop\diplom\backend')

from app.database import SessionLocal
from app.models.mouse import Mouse

db = SessionLocal()
mice = db.query(Mouse).filter(Mouse.citilink_sku != None).all()
print(f'Всего мышей с Ситилинк: {len(mice)}')
print()
print(f"{'ID':>4}  {'Название':<50}  {'Цена':>7}  {'DPI':>6}  {'Кноп':>4}  {'RGB':>3}  {'Source'}")
print('-' * 110)
for m in mice:
    print(
        f"{m.id:>4}  {(m.name or '')[:50]:<50}  "
        f"{m.citilink_price or 0:>7.0f}  "
        f"{m.max_dpi or 0:>6}  "
        f"{m.button_count or 0:>4}  "
        f"{'да' if m.has_rgb else 'нет':>3}  "
        f"{m.source}"
    )
db.close()
