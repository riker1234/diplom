import sys, json, requests
sys.stdout.reconfigure(encoding='utf-8')

# Follow the redirect
print("=== Following the 307 redirect ===")
r = requests.get(
    "https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2",
    params={"url": "/product/igrovaya-mysh-logitech-g502-x/"},
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "ru-RU,ru;q=0.9",
    },
    timeout=30,
    allow_redirects=True,
)
print(f"Final status: {r.status_code}")
print(f"Final URL: {r.url}")
ct = r.headers.get("content-type", "")
print(f"Content-Type: {ct}")
if "json" in ct and r.status_code == 200:
    data = r.json()
    print(f"Keys: {list(data.keys())}")
else:
    print(f"Body (first 500): {r.text[:500]}")
