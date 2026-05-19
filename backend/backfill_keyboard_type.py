"""Backfill keyboard_type for existing keyboards from Ozon and WB CDN."""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'C:\Users\User\Desktop\diplom\backend')

from app.database import SessionLocal
from app.models.keyboard import Keyboard
from app.parsers.ozon import _fetch_details as oz_fetch, _map_keyboard as oz_map
from app.parsers.wildberries import _fetch_details as wb_fetch, _map_keyboard as wb_map

db = SessionLocal()
kbs = db.query(Keyboard).filter(Keyboard.keyboard_type == None).all()
print(f"Keyboards without keyboard_type: {len(kbs)}")

# ── Ozon backfill ─────────────────────────────────────────────────────────────
oz_rows = [(k, int(k.ozon_sku)) for k in kbs if k.ozon_sku and k.ozon_sku.isdigit() and k.ozon_url]
url_map = {pid: row.ozon_url.replace("https://www.ozon.ru", "") for row, pid in oz_rows}
oz_details = oz_fetch([pid for _, pid in oz_rows], url_map)
oz_updated = 0
for row, pid in oz_rows:
    opts = oz_details.get(pid)
    if not opts:
        continue
    chars = oz_map(opts)
    if chars.get("keyboard_type"):
        row.keyboard_type = chars["keyboard_type"]
        oz_updated += 1
db.commit()
print(f"Ozon updated: {oz_updated}")

# ── WB backfill ───────────────────────────────────────────────────────────────
wb_rows = [(k, int(k.wb_sku)) for k in kbs if k.wb_sku and k.wb_sku.isdigit() and not k.keyboard_type]
wb_pids = [pid for _, pid in wb_rows]
wb_details = wb_fetch(wb_pids)
wb_updated = 0
for row, pid in wb_rows:
    opts = wb_details.get(pid)
    if not opts:
        continue
    chars = wb_map(opts)
    if chars.get("keyboard_type"):
        row.keyboard_type = chars["keyboard_type"]
        wb_updated += 1
db.commit()
print(f"WB updated: {wb_updated}")

# ── Fallback: derive from name ────────────────────────────────────────────────
# For keyboards still missing type, infer from product name
derived = 0
for k in db.query(Keyboard).filter(Keyboard.keyboard_type == None).all():
    name_low = (k.name or "").lower()
    if "мембранн" in name_low:
        k.keyboard_type = "Мембранная"
        derived += 1
    elif "механическ" in name_low or k.switches:
        k.keyboard_type = "Механическая"
        derived += 1
    elif "магнитн" in name_low or "magnetic" in name_low:
        k.keyboard_type = "Магнитно-механическая"
        derived += 1
db.commit()
print(f"Derived from name: {derived}")

# ── Summary ───────────────────────────────────────────────────────────────────
total = db.query(Keyboard).count()
filled = db.query(Keyboard).filter(Keyboard.keyboard_type != None).count()
print(f"\nResult: {filled}/{total} keyboards have keyboard_type")

vals = db.execute(__import__('sqlalchemy').text(
    "SELECT keyboard_type, count(*) FROM keyboards GROUP BY keyboard_type ORDER BY count(*) DESC"
)).fetchall()
for val, cnt in vals:
    print(f"  {val or 'NULL':<25} {cnt}")

db.close()
