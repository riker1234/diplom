"""Пагинация через ?page= и характеристики товара."""
import sys, requests, re, json
sys.stdout.reconfigure(encoding='utf-8')

H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html",
    "Accept-Language": "ru-RU,ru;q=0.9",
}

def get_products_from_page(url):
    r = requests.get(url, headers=H, timeout=15)
    if r.status_code != 200:
        return [], r.status_code
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
    if not m:
        return [], 0
    data = json.loads(m.group(1))
    try:
        products = data["props"]["pageProps"]["initialState"]["subcategory"]["productsFilter"]["payload"]["productsFilter"]["products"]
        return products, 200
    except (KeyError, TypeError):
        return [], 0

# Пагинация
for page in [1, 2, 3]:
    url = f"https://www.citilink.ru/catalog/myshi/?page={page}"
    products, status = get_products_from_page(url)
    ids = [p.get("id") for p in products]
    print(f"page={page} status={status} товаров={len(products)} ids={ids}")

# Страница конкретного товара — ищем характеристики
print("\n--- Характеристики товара ---")
slug = "mysh-oklik-202mw-chernyi-optich-1000dpi-besprov-usb-3but-2070314"
r = requests.get(f"https://www.citilink.ru/product/{slug}/", headers=H, timeout=15)
print(f"status={r.status_code}")
if r.status_code == 200:
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
    if m:
        data = json.loads(m.group(1))
        ps = data["props"]["pageProps"]["initialState"]
        print(f"keys: {list(ps.keys())}")
        prod = ps.get("product", {})
        print(f"product keys: {list(prod.keys())[:20]}")
        # Ищем характеристики
        for k in ["properties", "specs", "characteristics", "attributes", "params"]:
            if k in prod:
                print(f"\nprod['{k}']: {json.dumps(prod[k], ensure_ascii=False)[:500]}")
        # Углубляемся в payload
        for k, v in prod.items():
            if isinstance(v, dict) and "payload" in v:
                payload = v["payload"]
                if isinstance(payload, dict):
                    print(f"\nprod.{k}.payload keys: {list(payload.keys())[:15]}")
                    for pk, pv in payload.items():
                        if isinstance(pv, list) and pv:
                            print(f"  List '{pk}' len={len(pv)}: {json.dumps(pv[0], ensure_ascii=False)[:200]}")
