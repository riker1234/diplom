import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
os.environ['DATABASE_URL'] = open('.env').read().split('DATABASE_URL=')[1].split()[0]

from app.database import SessionLocal
from app.models.mouse import Mouse

db = SessionLocal()

# Ищем конкретный товар
m = db.query(Mouse).filter(Mouse.wb_sku == '335655717').first()
if m:
    print(f'Нашли: {m.name}')
    print(f'  weight_g: {m.weight_g}')
    print(f'  sensor: {m.sensor}')
    print(f'  connection_types: {m.connection_types}')
    print(f'  updated_at: {m.updated_at}')
else:
    print('Товар 335655717 не найден в БД')

# Сколько всего с заполненным sensor среди последних обновлённых
print('\n--- 10 последних обновлённых мышей ---')
mice = db.query(Mouse).order_by(Mouse.updated_at.desc()).limit(10).all()
for m in mice:
    print(f'{m.name[:40]:40} | w={m.weight_g} | s={m.sensor} | c={m.connection_types}')

db.close()
