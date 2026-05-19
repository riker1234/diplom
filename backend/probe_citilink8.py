"""Проверяем: можно ли получить характеристики через plain HTTP (без Selenium)?"""
import sys, requests, re, json
sys.stdout.reconfigure(encoding='utf-8')

H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html",
    "Accept-Language": "ru-RU,ru;q=0.9",
}

url = "https://www.citilink.ru/product/mysh-a4tech-bloody-l65-max-igrovaya-opticheskaya-provodnaya-usb-belyi-1874606/properties/"
r = requests.get(url, headers=H, timeout=15)
print(f"status={r.status_code}, len={len(r.text)}")

m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.DOTALL)
if not m:
    print("Нет __NEXT_DATA__")
    sys.exit()

data = json.loads(m.group(1))
pp = data["props"]["pageProps"]["initialState"].get("productPage", {})
props = pp.get("properties", {})
print(f"properties.isPending={props.get('isPending')}, payload keys={list((props.get('payload') or {}).keys())}")

# Ищем характеристики в HTML напрямую (они могут быть в тексте HTML)
# Ищем паттерн PropertiesName/PropertiesValue в HTML
names = re.findall(r'PropertiesName[^>]*>([^<]{2,60})</[^>]+>', r.text)
values = re.findall(r'PropertiesValue[^>]*>([^<]{1,200})</[^>]+>', r.text)
print(f"\nНайдено PropertiesName: {len(names)}, PropertiesValue: {len(values)}")
for n, v in zip(names[:15], values[:15]):
    print(f"  {n.strip()!r}: {v.strip()!r}")
