"""Исследуем структуру товара и ищем API для загрузки полного списка."""
import sys, requests, re, json
sys.stdout.reconfigure(encoding='utf-8')

H_html = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html",
    "Accept-Language": "ru-RU,ru;q=0.9",
}
H_json = {**H_html, "Accept": "application/json"}

# --- Смотрим структуру одного товара из SSR ---
r = requests.get("https://www.citilink.ru/catalog/myshi/", headers=H_html, timeout=15)
m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
data = json.loads(m.group(1))
products = data["props"]["pageProps"]["initialState"]["subcategory"]["productsFilter"]["payload"]["productsFilter"]["products"]
print(f"Товаров в SSR: {len(products)}")
p = products[0]
print(f"\nПервый товар:")
print(json.dumps(p, ensure_ascii=False, indent=2)[:1500])

# --- Пробуем API пагинации ---
print("\n\n--- Пробуем API для полного списка ---")
slug_id = p.get("id", "")

# Вариант 1: GraphQL
try:
    gql = requests.post(
        "https://www.citilink.ru/api/graphql/",
        json={"query": "{ productList(categorySlug: \"myshi\", limit: 10) { items { id name } } }"},
        headers={**H_json, "Content-Type": "application/json"},
        timeout=8
    )
    print(f"GraphQL: {gql.status_code} {gql.text[:150]!r}")
except Exception as e:
    print(f"GraphQL ERR: {e}")

# Вариант 2: Стандартный REST
for url, label in [
    ("https://www.citilink.ru/api/catalog/subcategory/myshi/products/?limit=10&offset=0", "REST subcategory"),
    ("https://www.citilink.ru/api/v1/product/?category=myshi&limit=10", "REST v1 product"),
    (f"https://www.citilink.ru/product/{p.get('slug','')}/", "Страница товара"),
]:
    try:
        rr = requests.get(url, headers=H_json, timeout=8)
        ct = rr.headers.get("content-type","")
        print(f"[{rr.status_code}] {label} ({ct[:40]})")
        if rr.status_code == 200 and "json" in ct:
            dd = rr.json()
            print(f"  Keys: {list(dd.keys())[:10]}")
        elif rr.status_code == 200:
            # Ищем характеристики в HTML товара
            mm = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', rr.text, re.DOTALL)
            if mm:
                pd = json.loads(mm.group(1))
                ps = pd.get("props",{}).get("pageProps",{}).get("initialState",{})
                prod_keys = list(ps.keys())
                print(f"  pageProps.initialState keys: {prod_keys[:10]}")
                if "product" in ps:
                    prod = ps["product"]
                    print(f"  product keys: {list(prod.keys())[:15]}")
    except Exception as e:
        print(f"  ERR: {e}")
