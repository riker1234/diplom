"""Копаем глубже в __NEXT_DATA__ Ситилинка."""
import sys, requests, re, json
sys.stdout.reconfigure(encoding='utf-8')

H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html",
    "Accept-Language": "ru-RU,ru;q=0.9",
}

r = requests.get("https://www.citilink.ru/catalog/myshi/", headers=H, timeout=15)
m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
if not m:
    print("__NEXT_DATA__ не найден")
    sys.exit()

data = json.loads(m.group(1))
state = data["props"]["pageProps"]["initialState"]

# Смотрим subcategory
sub = state.get("subcategory", {})
print(f"subcategory keys: {list(sub.keys())[:20]}")

for k, v in sub.items():
    if isinstance(v, list) and len(v) > 2:
        print(f"\nList '{k}' len={len(v)}")
        if isinstance(v[0], dict):
            print(f"  first item keys: {list(v[0].keys())[:12]}")
            print(f"  first item: {json.dumps(v[0], ensure_ascii=False)[:300]}")
    elif isinstance(v, dict) and v:
        print(f"\nDict '{k}' keys: {list(v.keys())[:12]}")

# Ищем слово "items" или "products" в глубину
def find_products(obj, path="", depth=0):
    if depth > 4:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("items", "products", "data", "товары") and isinstance(v, list) and len(v) > 2:
                print(f"\n>>> Нашли список по пути '{path}.{k}', len={len(v)}")
                if isinstance(v[0], dict):
                    print(f"    keys: {list(v[0].keys())[:12]}")
                    print(f"    first: {json.dumps(v[0], ensure_ascii=False)[:400]}")
            else:
                find_products(v, f"{path}.{k}", depth+1)
    elif isinstance(obj, list) and len(obj) > 2 and isinstance(obj[0], dict):
        if any(k in obj[0] for k in ("id", "name", "price", "sku")):
            print(f"\n>>> Нашли список товаров по пути '{path}', len={len(obj)}")
            print(f"    keys: {list(obj[0].keys())[:12]}")

find_products(state)
