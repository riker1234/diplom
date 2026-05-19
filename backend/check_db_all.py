import sys, os
sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r'C:\Users\User\Desktop\diplom\backend')
from app.database import SessionLocal
from app.models.mouse import Mouse
from app.models.keyboard import Keyboard
from app.models.monitor import Monitor
from app.models.headphones import Headphones
from app.models.microphone import Microphone
from app.models.mousepad import Mousepad

db = SessionLocal()

# ── Мыши ──────────────────────────────────────────────────────────────────────
mice = db.query(Mouse).all()
print(f"\n{'='*120}")
print(f"МЫШИ: {len(mice)} шт.")
print(f"{'Название':38} | {'Цена':6} | {'Сенсор':22} | {'Подключение':18} | {'Кнопки':6} | {'DPI':6} | {'Цвет':10} | RGB")
print("-" * 120)
for m in mice:
    print(f"{(m.name or '')[:38]:38} | {(m.price or 0):6.0f} | {(m.sensor or '-')[:22]:22} | "
          f"{(m.connection_types or '-')[:18]:18} | {str(m.button_count or '-'):6} | "
          f"{str(m.max_dpi or '-'):6} | {(m.color or '-')[:10]:10} | {m.has_rgb}")

# ── Клавиатуры ────────────────────────────────────────────────────────────────
keyboards = db.query(Keyboard).all()
print(f"\n{'='*120}")
print(f"КЛАВИАТУРЫ: {len(keyboards)} шт.")
print(f"{'Название':38} | {'Цена':6} | {'Свитчи':20} | {'Подключение':18} | {'Форм-фактор':14} | {'Раскладка':12} | RGB")
print("-" * 120)
for k in keyboards:
    print(f"{(k.name or '')[:38]:38} | {(k.price or 0):6.0f} | {(k.switches or '-')[:20]:20} | "
          f"{(k.connection_types or '-')[:18]:18} | {(k.form_factor or '-')[:14]:14} | "
          f"{(k.layout or '-')[:12]:12} | {k.has_rgb}")

# ── Мониторы ──────────────────────────────────────────────────────────────────
monitors = db.query(Monitor).all()
print(f"\n{'='*120}")
print(f"МОНИТОРЫ: {len(monitors)} шт.")
print(f"{'Название':38} | {'Цена':6} | {'Диаг':5} | {'Разреш':10} | {'Матрица':8} | {'Герц':5} | {'Отклик':7} | HDR")
print("-" * 120)
for m in monitors:
    print(f"{(m.name or '')[:38]:38} | {(m.price or 0):6.0f} | {str(m.diagonal_inch or '-'):5} | "
          f"{(m.resolution or '-')[:10]:10} | {(m.matrix_type or '-')[:8]:8} | "
          f"{str(m.refresh_rate_hz or '-'):5} | {str(m.response_time_ms or '-'):7} | {m.hdr}")

# ── Наушники ──────────────────────────────────────────────────────────────────
headphones = db.query(Headphones).all()
print(f"\n{'='*120}")
print(f"НАУШНИКИ: {len(headphones)} шт.")
print(f"{'Название':38} | {'Цена':6} | {'Конструкция':16} | {'Подключение':18} | {'Импеданс':8} | {'Частоты':12} | Mic")
print("-" * 120)
for h in headphones:
    print(f"{(h.name or '')[:38]:38} | {(h.price or 0):6.0f} | {(h.construction_type or '-')[:16]:16} | "
          f"{(h.connection_types or '-')[:18]:18} | {str(h.impedance_ohm or '-'):8} | "
          f"{(h.frequency_response or '-')[:12]:12} | {h.has_microphone}")

# ── Микрофоны ─────────────────────────────────────────────────────────────────
microphones = db.query(Microphone).all()
print(f"\n{'='*120}")
print(f"МИКРОФОНЫ: {len(microphones)} шт.")
print(f"{'Название':38} | {'Цена':6} | {'Тип':18} | {'Подключение':18} | {'Направленность':16} | {'Частоты':14}")
print("-" * 120)
for m in microphones:
    print(f"{(m.name or '')[:38]:38} | {(m.price or 0):6.0f} | {(m.mic_type or '-')[:18]:18} | "
          f"{(m.connection_types or '-')[:18]:18} | {(m.directionality or '-')[:16]:16} | "
          f"{(m.frequency_range or '-')[:14]:14}")

# ── Коврики ───────────────────────────────────────────────────────────────────
mousepads = db.query(Mousepad).all()
print(f"\n{'='*120}")
print(f"КОВРИКИ: {len(mousepads)} шт.")
print(f"{'Название':38} | {'Цена':6} | {'Размер':14} | {'Материал':20} | {'Жёсткость':12} | {'Толщ':5} | RGB")
print("-" * 120)
for p in mousepads:
    print(f"{(p.name or '')[:38]:38} | {(p.price or 0):6.0f} | {(p.size or '-')[:14]:14} | "
          f"{(p.surface_material or '-')[:20]:20} | {(p.hardness or '-')[:12]:12} | "
          f"{str(p.thickness_mm or '-'):5} | {p.has_rgb}")

# ── Итог ──────────────────────────────────────────────────────────────────────
print(f"\n{'='*120}")
total = len(mice) + len(keyboards) + len(monitors) + len(headphones) + len(microphones) + len(mousepads)
print(f"ИТОГО: {total} товаров в БД")
print(f"  Мыши: {len(mice)}, Клавиатуры: {len(keyboards)}, Мониторы: {len(monitors)}, "
      f"Наушники: {len(headphones)}, Микрофоны: {len(microphones)}, Коврики: {len(mousepads)}")

db.close()
