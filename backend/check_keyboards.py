"""Просмотр клавиатур в БД."""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'C:\Users\User\Desktop\diplom\backend')

from app.database import SessionLocal
from app.models.keyboard import Keyboard

db = SessionLocal()
kbs = db.query(Keyboard).order_by(Keyboard.id).all()
print(f'Всего клавиатур: {len(kbs)}')
print()
print(f"{'ID':>4}  {'Название':<48}  {'Цена':>7}  {'Switches':<18}  {'RGB':>3}  {'Source'}")
print('-' * 115)
for k in kbs:
    price = k.price or k.wb_price or k.dns_price or k.citilink_price or 0
    sw = (k.switches or '-')[:18]
    print(
        f"{k.id:>4}  {(k.name or '')[:48]:<48}  "
        f"{price:>7.0f}  "
        f"{sw:<18}  "
        f"{'да' if k.has_rgb else 'нет':>3}  "
        f"{k.source}"
    )
db.close()
