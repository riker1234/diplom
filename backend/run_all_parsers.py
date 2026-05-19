import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
os.environ.setdefault("DATABASE_URL", open(".env").read().split("DATABASE_URL=")[1].split()[0])

import app.parsers.ozon as oz
from app.database import SessionLocal

# прогрев браузера — убедимся что сессия живая
print("Прогрев браузера...")
driver = oz._get_driver()
print(f"  URL: {driver.current_url}")
test = oz._search_ozon("клавиатура механическая", 2)
print(f"  тест-запрос: {len(test)} товаров")
if not test:
    print("  ОШИБКА: Ozon не отвечает, прерываю")
    driver.quit()
    import sys; sys.exit(1)

db = SessionLocal()

parsers = [
    ("keyboards",   oz.parse_keyboards),
    ("monitors",    oz.parse_monitors),
    ("headphones",  oz.parse_headphones),
    ("microphones", oz.parse_microphones),
    ("mousepads",   oz.parse_mousepads),
]

for name, fn in parsers:
    print(f"\n{'='*50}")
    print(f"Парсинг: {name}...")
    try:
        result = fn(db)
        print(f"  added={result['added']}  updated={result['updated']}  "
              f"failed={result.get('failed',0)}  skipped={result.get('skipped',0)}")
    except Exception as e:
        print(f"  ОШИБКА: {e}")

db.close()
print("\nГотово!")
