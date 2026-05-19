"""Просмотр всех категорий кроме мышей."""
import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'C:\Users\User\Desktop\diplom\backend')

from app.database import SessionLocal
from app.models.keyboard import Keyboard
from app.models.monitor import Monitor
from app.models.headphones import Headphones
from app.models.microphone import Microphone
from app.models.mousepad import Mousepad

db = SessionLocal()

# ── Мониторы ──────────────────────────────────────────────────────────────────
mons = db.query(Monitor).order_by(Monitor.id).all()
print(f"\n{'='*108}")
print(f"  МОНИТОРЫ: {len(mons)} шт.")
print(f"{'='*108}")
print(f"{'ID':>4}  {'Название':<44}  {'Цена':>7}  {'Диаг':>5}  {'Разрешение':<12}  {'Гц':>4}  Source")
print('-'*108)
for m in mons:
    price = m.price or m.wb_price or m.dns_price or m.citilink_price or 0
    diag = f'{m.diagonal_inch:.0f}"' if m.diagonal_inch else '-'
    res = (m.resolution or '-')[:12]
    hz = m.refresh_rate_hz or 0
    print(f"{m.id:>4}  {(m.name or '')[:44]:<44}  {price:>7.0f}  {diag:>5}  {res:<12}  {hz:>4}  {m.source}")

# ── Наушники ──────────────────────────────────────────────────────────────────
heads = db.query(Headphones).order_by(Headphones.id).all()
print(f"\n{'='*108}")
print(f"  НАУШНИКИ: {len(heads)} шт.")
print(f"{'='*108}")
print(f"{'ID':>4}  {'Название':<44}  {'Цена':>7}  {'Конструкция':<16}  {'Mic':>3}  {'RGB':>3}  Source")
print('-'*108)
for h in heads:
    price = h.price or h.wb_price or h.dns_price or h.citilink_price or 0
    ct = (h.construction_type or '-')[:16]
    print(f"{h.id:>4}  {(h.name or '')[:44]:<44}  {price:>7.0f}  {ct:<16}  {'да' if h.has_microphone else 'нет':>3}  {'да' if h.has_rgb else 'нет':>3}  {h.source}")

# ── Микрофоны ─────────────────────────────────────────────────────────────────
mics = db.query(Microphone).order_by(Microphone.id).all()
print(f"\n{'='*108}")
print(f"  МИКРОФОНЫ: {len(mics)} шт.")
print(f"{'='*108}")
print(f"{'ID':>4}  {'Название':<44}  {'Цена':>7}  {'Тип':<16}  {'Направленность':<18}  Source")
print('-'*108)
for m in mics:
    price = m.price or m.wb_price or m.dns_price or m.citilink_price or 0
    mt = (m.mic_type or '-')[:16]
    dr = (m.directionality or '-')[:18]
    print(f"{m.id:>4}  {(m.name or '')[:44]:<44}  {price:>7.0f}  {mt:<16}  {dr:<18}  {m.source}")

# ── Коврики ───────────────────────────────────────────────────────────────────
pads = db.query(Mousepad).order_by(Mousepad.id).all()
print(f"\n{'='*108}")
print(f"  КОВРИКИ: {len(pads)} шт.")
print(f"{'='*108}")
print(f"{'ID':>4}  {'Название':<44}  {'Цена':>7}  {'Размер':<14}  {'Материал':<16}  {'RGB':>3}  Source")
print('-'*108)
for p in pads:
    price = p.price or p.wb_price or p.dns_price or p.citilink_price or 0
    sz = (p.size or '-')[:14]
    mat = (p.surface_material or '-')[:16]
    print(f"{p.id:>4}  {(p.name or '')[:44]:<44}  {price:>7.0f}  {sz:<14}  {mat:<16}  {'да' if p.has_rgb else 'нет':>3}  {p.source}")

db.close()
