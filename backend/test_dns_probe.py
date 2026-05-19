"""
Проверяем DNS microdata endpoint: https://www.dns-shop.ru/product/microdata/{id}/
Шаг 1 — проверяем доступность без браузера (requests)
Шаг 2 — пробуем получить product_id из категории
"""
import sys, json, re, time, requests
sys.stdout.reconfigure(encoding='utf-8')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "ru-RU,ru;q=0.9",
}

# ── Шаг 1: microdata с известным ID ───────────────────────────────────────────
known_ids = [
    "0c89fbb3b22f4a52b9a6",  # пример из кэша
    "1f2e3d4c5b6a79880000",  # вымышленный — проверим формат 404
]

print("=== Шаг 1: microdata endpoint (requests) ===")
for pid in known_ids:
    url = f"https://www.dns-shop.ru/product/microdata/{pid}/"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        print(f"ID={pid}: status={r.status_code}, len={len(r.content)}")
        if r.status_code == 200:
            print(f"  Content-Type: {r.headers.get('Content-Type','')}")
            print(f"  Body[:300]: {r.text[:300]}")
        elif r.status_code in (301, 302, 401, 403):
            print(f"  Headers: {dict(list(r.headers.items())[:4])}")
    except Exception as e:
        print(f"ID={pid}: ERROR {e}")

# ── Шаг 2: категория через requests ───────────────────────────────────────────
print("\n=== Шаг 2: категория мышей (requests) ===")
cat_url = "https://www.dns-shop.ru/catalog/17a8a01d16404e77/myshi/"
try:
    r = requests.get(cat_url, headers=HEADERS, timeout=10)
    print(f"Status={r.status_code}, len={len(r.content)}")
    if r.status_code == 200:
        ids = re.findall(r'/product/([a-f0-9]{20})/', r.text)
        ids = list(dict.fromkeys(ids))
        print(f"product IDs: {len(ids)}, первые: {ids[:5]}")

        if ids:
            pid = ids[0]
            print(f"\n=== Шаг 3: microdata для ID={pid} ===")
            murl = f"https://www.dns-shop.ru/product/microdata/{pid}/"
            mr = requests.get(murl, headers=HEADERS, timeout=10)
            print(f"Status: {mr.status_code}, CT: {mr.headers.get('Content-Type','')}")
            if mr.status_code == 200:
                print(f"Body[:800]:\n{mr.text[:800]}")
                try:
                    data = mr.json()
                    print(f"\nJSON keys: {list(data.keys())}")
                    print(json.dumps(data, ensure_ascii=False, indent=2)[:1500])
                except Exception:
                    print("(не JSON)")
    else:
        print(f"Заблокировано: {r.status_code}")
except Exception as e:
    print(f"Ошибка: {e}")

# ── Шаг 4: поиск ──────────────────────────────────────────────────────────────
print("\n=== Шаг 4: поиск (requests) ===")
for surl in [
    "https://www.dns-shop.ru/search/?q=logitech+g502",
    "https://www.dns-shop.ru/catalog/17a8a01d16404e77/myshi/?order=4&groupBy=none",
]:
    try:
        r = requests.get(surl, headers=HEADERS, timeout=10, allow_redirects=True)
        ids = re.findall(r'/product/([a-f0-9]{20})/', r.text) if r.status_code == 200 else []
        ids = list(dict.fromkeys(ids))
        print(f"{r.status_code} {surl[-55:]!r} → {len(ids)} IDs")
        if ids:
            print(f"  Примеры: {ids[:3]}")
    except Exception as e:
        print(f"ERROR: {e}")
