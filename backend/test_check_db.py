import sys; sys.stdout.reconfigure(encoding='utf-8')
import os; os.environ['DATABASE_URL'] = open('.env').read().split('DATABASE_URL=')[1].split()[0]
from app.database import SessionLocal
from app.models.mouse import Mouse
db = SessionLocal()
mice = db.query(Mouse).all()
print(f"Total: {len(mice)}")
print(f"{'Name':40} | {'Price':7} | {'Sensor':25} | {'Conn':15} | {'Btn':3} | {'DPI':6} | {'Color':10} | {'Form':12} | RGB")
print("-" * 140)
for m in mice:
    sensor = (m.sensor or "-")[:25]
    conn = (m.connection_types or "-")[:15]
    color = (m.color or "-")[:10]
    form = (m.form_factor or "-")[:12]
    print(f"{m.name[:40]:40} | {m.price:7.0f} | {sensor:25} | {conn:15} | {str(m.button_count or '-'):3} | {str(m.max_dpi or '-'):6} | {color:10} | {form:12} | {m.has_rgb}")
db.close()
