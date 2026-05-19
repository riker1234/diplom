import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'C:\Users\User\Desktop\diplom\backend')

from app.database import SessionLocal
from app.models.keyboard import Keyboard

db = SessionLocal()
kbs = db.query(Keyboard).filter(Keyboard.wb_sku != None).all()
print(f'WB keyboards: {len(kbs)}')
null_sw = sum(1 for k in kbs if not k.switches)
null_ct = sum(1 for k in kbs if not k.connection_types)
print(f'switches null: {null_sw}/{len(kbs)}')
print(f'connection_types null: {null_ct}/{len(kbs)}')
print()
for k in kbs[:8]:
    name = (k.name or '')[:40]
    print(f'{k.wb_sku} | sw={k.switches!r} | ct={k.connection_types!r} | {name}')
db.close()
