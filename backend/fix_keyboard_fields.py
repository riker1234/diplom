"""Fix keyboard connection_types (normalize) + backfill switches via CDN."""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'C:\Users\User\Desktop\diplom\backend')

from app.database import SessionLocal
from app.models.keyboard import Keyboard
from app.parsers.wildberries import (
    _normalize_connection_type, _fetch_details as wb_fetch, _map_keyboard as wb_map_kb
)
from app.parsers.ozon import (
    backfill_keyboards as oz_backfill
)

db = SessionLocal()

# ── 1. Normalize connection_types for ALL existing keyboards ──────────────────
fixed_ct = 0
for k in db.query(Keyboard).all():
    ct = k.connection_types
    if not ct:
        continue
    normalized = _normalize_connection_type(ct)
    if normalized != ct:
        k.connection_types = normalized
        fixed_ct += 1
db.commit()
print(f"Normalized connection_types: {fixed_ct} records")

# ── 2. Backfill switches for Ozon keyboards ───────────────────────────────────
print("\nBackfilling Ozon keyboard switches...")
try:
    result = oz_backfill(db)
    print(f"Ozon: {result}")
except Exception as e:
    print(f"Ozon backfill error: {e}")

# ── 3. Backfill switches for WB keyboards ─────────────────────────────────────
print("\nBackfilling WB keyboard switches...")
try:
    wb_rows = db.query(Keyboard).filter(
        Keyboard.switches == None,
        Keyboard.wb_sku != None,
    ).all()
    print(f"  WB keyboards with null switches: {len(wb_rows)}")

    pids = []
    pid_to_row = {}
    for row in wb_rows:
        if row.wb_sku and str(row.wb_sku).isdigit():
            pid = int(row.wb_sku)
            pids.append(pid)
            pid_to_row[pid] = row

    details = wb_fetch(pids)
    updated = failed = skipped = 0
    for pid, row in pid_to_row.items():
        opts = details.get(pid)
        if not opts:
            skipped += 1
            continue
        try:
            chars = wb_map_kb(opts)
            for field, value in chars.items():
                if value is not None:
                    setattr(row, field, value)
            db.commit()
            updated += 1
        except Exception as ex:
            failed += 1
            db.rollback()
    print(f"  WB: updated={updated}, skipped={skipped}, failed={failed}")
except Exception as e:
    print(f"WB backfill error: {e}")

db.close()

# ── Summary ───────────────────────────────────────────────────────────────────
from app.database import SessionLocal as SL2
from app.models.keyboard import Keyboard as KB
db2 = SL2()
kbs = db2.query(KB).all()
null_sw = sum(1 for k in kbs if not k.switches)
null_ct = sum(1 for k in kbs if not k.connection_types)
print(f"\nAfter fix — {len(kbs)} keyboards: switches null={null_sw}, connection_types null={null_ct}")
db2.close()
