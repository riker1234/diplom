"""Ищем полные характеристики в plain HTML по всем возможным классам."""
import sys, requests, re
sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup

H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html", "Accept-Language": "ru-RU,ru;q=0.9",
}

url = "https://www.citilink.ru/product/mysh-a4tech-bloody-l65-max-igrovaya-opticheskaya-provodnaya-usb-belyi-1874606/properties/"
r = requests.get(url, headers=H, timeout=15)
html = r.text
soup = BeautifulSoup(html, "html.parser")

# Ищем конкретные поля из скриншота в HTML
for field in ["Тип соединения мыши", "Разрешение сенсора", "Количество кнопок", "Хват", "Подсветка", "Вес"]:
    if field in html:
        print(f"✓ '{field}' ЕСТЬ в plain HTML")
    else:
        print(f"✗ '{field}' отсутствует в plain HTML")

# Ищем все классы содержащие "ropert" или "roperti" в HTML
all_classes = re.findall(r'class="([^"]*(?:ropert|roperti|ropert)[^"]*)"', html)
unique = sorted(set(all_classes))
print(f"\nУникальных классов с 'ropert': {len(unique)}")
for c in unique[:20]:
    print(f"  {c[:90]}")

# Пробуем PropertiesItem (без "Product")
items = soup.find_all(class_=re.compile(r'(?<!Product)PropertiesItem'))
print(f"\nPropertiesItem (без Product): {len(items)}")
for item in items[:5]:
    print(f"  {item.get_text(strip=True)[:100]!r}")

# Ищем PropertiesNameWrapper / PropertiesName / PropertiesValue
for pattern in [r'PropertiesNameWrapper', r'--PropertiesName\b', r'--PropertiesValue\b',
                r'PropertiesItem\b', r'PropertyGroup']:
    found = soup.find_all(class_=re.compile(pattern))
    print(f"'{pattern}': {len(found)}")
    if found:
        print(f"  first text: {found[0].get_text(strip=True)[:80]!r}")
