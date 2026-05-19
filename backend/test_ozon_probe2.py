import sys, json, requests
sys.stdout.reconfigure(encoding='utf-8')

BASE = "https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2"
TEST_PRODUCT_URL = "/product/igrovaya-mysh-logitech-g502-x/"

headers_variants = [
    # Variant 1: minimal
    {"User-Agent": "python-requests/2.31.0", "Accept": "application/json"},
    # Variant 2: curl-like
    {"User-Agent": "curl/7.88.1"},
    # Variant 3: Googlebot
    {"User-Agent": "Googlebot/2.1 (+http://www.google.com/bot.html)"},
    # Variant 4: Yandex bot
    {"User-Agent": "YandexBot/3.0; +http://yandex.com/bots", "Accept": "application/json"},
]

print("=== Testing headers variants ===")
for i, h in enumerate(headers_variants):
    try:
        r = requests.get(BASE, params={"url": TEST_PRODUCT_URL}, headers=h, timeout=10, allow_redirects=False)
        ct = r.headers.get("content-type", "")
        print(f"Variant {i+1}: status={r.status_code}, content-type={ct}")
        if r.status_code == 200:
            print("SUCCESS! Keys:", list(r.json().keys())[:10])
        elif r.status_code in (301, 302, 303, 307, 308):
            print("Redirect to:", r.headers.get("Location", ""))
    except Exception as e:
        print(f"Variant {i+1}: Error - {e}")

# Also try composer endpoint
print("\n=== Testing composer endpoint ===")
try:
    r = requests.get(
        "https://www.ozon.ru/api/composer-api.bx/page/json/v2",
        params={"url": TEST_PRODUCT_URL},
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
        timeout=10,
        allow_redirects=False,
    )
    print(f"composer: status={r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print("Keys:", list(data.keys())[:10])
except Exception as e:
    print(f"composer error: {e}")

# Check if it's truly blocked by the IP or just needs cookies
print("\n=== Testing with Accept-Language only ===")
try:
    r = requests.get(
        BASE,
        params={"url": "/"},
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Accept-Language": "ru",
        },
        timeout=10,
        allow_redirects=False,
    )
    print(f"Homepage JSON: status={r.status_code}, content-type={r.headers.get('content-type', '')}")
    if r.status_code == 200:
        print("Keys:", list(r.json().keys())[:10])
    else:
        print("Body (first 200):", r.text[:200])
except Exception as e:
    print(f"Error: {e}")

# Test a known Ozon product ID directly
print("\n=== Test known product IDs ===")
# Logitech G502 X is 1097337765 on Ozon
for pid in ["1097337765", "306582990"]:
    url = f"https://www.ozon.ru/product/{pid}/"
    try:
        r = requests.get(
            "https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2",
            params={"url": f"/product/{pid}/"},
            headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
            timeout=10,
            allow_redirects=False,
        )
        print(f"Product {pid}: status={r.status_code}")
    except Exception as e:
        print(f"Product {pid}: {e}")
