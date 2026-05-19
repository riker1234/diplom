"""Ищем рабочий JSON-эндпоинт Ситилинк (Next.js app)."""
import sys, requests, re
sys.stdout.reconfigure(encoding='utf-8')

H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": "https://www.citilink.ru/",
}

def probe(label, url, params=None):
    try:
        r = requests.get(url, headers=H, params=params, timeout=10)
        ct = r.headers.get("content-type", "")
        is_json = "json" in ct
        print(f"[{r.status_code}] {label}")
        if r.status_code == 200 and is_json:
            data = r.json()
            if isinstance(data, dict):
                print(f"  Keys: {list(data.keys())[:12]}")
                # Ищем список товаров
                for k, v in data.items():
                    if isinstance(v, list) and v:
                        print(f"  List '{k}' len={len(v)}, first item keys: {list(v[0].keys())[:8] if isinstance(v[0], dict) else type(v[0])}")
            elif isinstance(data, list):
                print(f"  List len={len(data)}")
        elif r.status_code == 200:
            print(f"  HTML, len={len(r.text)}")
        else:
            print(f"  {r.text[:100]!r}")
    except Exception as e:
        print(f"  ERR: {e}")

# Next.js data endpoints (buildId может быть любым — попробуем несколько)
probe("Next.js catalog /myshi/",
    "https://www.citilink.ru/_next/data/latest/catalog/myshi.json")

# Реальный внутренний API (видно в DevTools)
probe("Internal catalog API",
    "https://www.citilink.ru/api/catalog/",
    params={"category_id": 489, "limit": 12, "offset": 0, "sort": "relevance"})

probe("Internal search",
    "https://www.citilink.ru/api/search/",
    params={"query": "игровая мышь", "limit": 10})

# Известный публичный API Ситилинка (встречается на GitHub)
probe("Public API products",
    "https://www.citilink.ru/catalog/myshi/",
    params={"view_type": "json"})

# Попытка получить __NEXT_DATA__ из HTML
print("\n--- Ищем __NEXT_DATA__ в HTML каталога ---")
try:
    H2 = {**H, "Accept": "text/html"}
    r = requests.get("https://www.citilink.ru/catalog/myshi/", headers=H2, timeout=10)
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
    if m:
        import json
        data = json.loads(m.group(1))
        # Ищем товары в дереве
        props = data.get("props", {}).get("pageProps", {})
        print(f"  pageProps keys: {list(props.keys())[:15]}")
        for k, v in props.items():
            if isinstance(v, list) and len(v) > 2:
                print(f"  List '{k}' len={len(v)}")
            elif isinstance(v, dict):
                print(f"  Dict '{k}' keys: {list(v.keys())[:8]}")
    else:
        print("  __NEXT_DATA__ не найден")
except Exception as e:
    print(f"  ERR: {e}")
