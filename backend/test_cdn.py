import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")

# Тест CDN card.json с конкретным мышиным товаром
import requests

DETAIL_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": "https://www.wildberries.ru/",
}

def get_basket(vol):
    thresholds = [
        143, 287, 431, 719, 1007, 1061, 1115, 1169, 1313, 1601,
        1655, 1919, 2045, 2189, 2405, 2621, 2837, 3053, 3269, 3485,
        3701, 3917, 4133, 4349,
    ]
    for i, t in enumerate(thresholds):
        if vol <= t:
            return str(i + 1).zfill(2)
    return "25"

def build_card_json_url(product_id):
    vol = product_id // 100000
    part = product_id // 1000
    basket = get_basket(vol)
    return f"https://basket-{basket}.wbbasket.ru/vol{vol}/part{part}/{product_id}/info/ru/card.json"

# Тестируем несколько известных товаров (мыши)
test_ids = [335655717, 280681270]

for pid in test_ids:
    url = build_card_json_url(pid)
    print(f"\n=== Product {pid} ===")
    print(f"URL: {url}")
    try:
        r = requests.get(url, headers=DETAIL_HEADERS, timeout=10)
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"Top-level keys: {list(data.keys())}")

            flat = list(data.get("options", []))
            for group in data.get("grouped_params", []):
                flat.extend(group.get("params", []))

            print(f"Total flat options after merge: {len(flat)}")
            for o in flat:
                print(f"  {o.get('name','?')} -> {o.get('value','?')}")
        else:
            print(f"Error response: {r.text[:200]}")
    except Exception as e:
        print(f"Exception: {e}")
