import requests

url = "https://www.wildberries.ru/__internal/u-card/cards/v4/detail"
params = {
    "appType": 1,
    "curr": "rub",
    "dest": -1257786,
    "spp": 30,
    "hide_vflags": 4294967296,
    "ab_testing": "false",
    "lang": "ru",
    "nm": "335655717"
}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://www.wildberries.ru/catalog/335655717/detail.aspx",
    "Accept": "*/*",
}

r = requests.get(url, params=params, headers=headers, timeout=15)
print("Status:", r.status_code)
if r.status_code == 200:
    data = r.json()
    products = data.get("data", {}).get("products", [])
    if products:
        p = products[0]
        opts = p.get("options", [])
        print("options count:", len(opts))
        for o in opts[:20]:
            print(" ", o)
    else:
        print("No products in response, keys:", list(data.keys()))
else:
    print("Response:", r.text[:500])
