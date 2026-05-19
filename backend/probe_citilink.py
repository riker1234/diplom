"""Проверяем доступность Ситилинк и форматы их API."""
import sys, json, requests
sys.stdout.reconfigure(encoding='utf-8')

H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html,*/*",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": "https://www.citilink.ru/",
}

def probe(label, url, **kwargs):
    try:
        r = requests.get(url, headers=H, timeout=10, **kwargs)
        ct = r.headers.get("content-type", "")
        print(f"\n[{r.status_code}] {label}")
        print(f"  URL: {url[:80]}")
        print(f"  Content-Type: {ct[:60]}")
        if r.status_code == 200:
            if "json" in ct:
                data = r.json()
                # Показываем верхние ключи
                if isinstance(data, dict):
                    print(f"  Keys: {list(data.keys())[:10]}")
                elif isinstance(data, list):
                    print(f"  List len={len(data)}, first keys: {list(data[0].keys())[:8] if data else []}")
            else:
                print(f"  Body preview: {r.text[:200]!r}")
        else:
            print(f"  Body: {r.text[:150]!r}")
    except Exception as e:
        print(f"\n[ERR] {label}: {e}")

# 1. Просто главная страница
probe("Главная", "https://www.citilink.ru/")

# 2. Каталог мышей — обычная страница
probe("Каталог мышей HTML", "https://www.citilink.ru/catalog/myshi/")

# 3. JSON API поиска (встречается в сетевых запросах браузера)
probe("Search API v1",
    "https://www.citilink.ru/api/v1/search/",
    params={"text": "игровая мышь", "offset": 0, "limit": 10, "category_id": 489})

# 4. Другой вариант search API
probe("Search API v2",
    "https://www.citilink.ru/search/",
    params={"text": "игровая мышь", "view_type": "list"})

# 5. Catalog API — JSON листинг категории
probe("Catalog JSON мыши",
    "https://www.citilink.ru/catalog/myshi/",
    headers={**H, "Accept": "application/json", "X-Requested-With": "XMLHttpRequest"})

# 6. Product listing API
probe("Product listing API",
    "https://www.citilink.ru/api/catalog/products/",
    params={"category_id": "489", "limit": 5})
