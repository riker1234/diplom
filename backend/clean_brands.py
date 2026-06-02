"""One-off cleanup: fix junk brand values (review counts, ratings, 'Ozon', bare numbers).

These came from the old Ozon parser grabbing the review-count label as brand
(e.g. '9 874', '232 отзыва'). Re-parsing does NOT fix existing rows, so this
script recomputes the brand for any row whose brand is not brand-like.

Run from the backend/ directory with DATABASE_URL pointing at the target DB:

    # prod (use Railway DATABASE_PUBLIC_URL)
    DATABASE_URL="postgresql+psycopg://postgres:PASS@HOST.proxy.rlwy.net:PORT/railway" python clean_brands.py

    # local (uses .env)
    python clean_brands.py
"""
import re

from app.database import SessionLocal
from app.models.mouse import Mouse
from app.models.keyboard import Keyboard
from app.models.monitor import Monitor
from app.models.headphones import Headphones
from app.models.microphone import Microphone
from app.models.mousepad import Mousepad
from app.parsers.ozon import _is_brand_like

_MODELS = [Mouse, Keyboard, Monitor, Headphones, Microphone, Mousepad]


def _brand_from_name(name: str) -> str | None:
    """Best-effort brand = first word of the name, if it looks like a brand.

    Peripheral brands are Latin (Logitech, Razer, JSHIX, Carrera, IO...).
    A Cyrillic first word is almost always a common noun/adjective
    ('Мышь', 'Игровая', 'Наушники') — not a brand, so we null those out.
    """
    if not name:
        return None
    first = name.strip().split()[0]
    if re.search(r"[а-яё]", first, re.IGNORECASE):
        return None
    if (len(first) > 1
            and not re.match(r"^\d+([.,]\d+)?$", first)
            and _is_brand_like(first)):
        return first
    return None


def main() -> None:
    db = SessionLocal()
    fixed = nulled = checked = 0
    try:
        for model in _MODELS:
            for row in db.query(model).all():
                brand = (row.brand or "").strip()
                if not brand or _is_brand_like(brand):
                    continue  # empty or already a real brand — leave it
                checked += 1
                new_brand = _brand_from_name(row.name or "")
                row.brand = new_brand
                if new_brand:
                    fixed += 1
                else:
                    nulled += 1
            db.commit()
        print(f"junk-брендов найдено: {checked} | пересчитано из имени: {fixed} | обнулено: {nulled}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
