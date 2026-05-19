"""Парсим характеристики через BeautifulSoup из plain HTML."""
import sys, requests, re, json
sys.stdout.reconfigure(encoding='utf-8')

from bs4 import BeautifulSoup

H = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html",
    "Accept-Language": "ru-RU,ru;q=0.9",
}

url = "https://www.citilink.ru/product/mysh-a4tech-bloody-l65-max-igrovaya-opticheskaya-provodnaya-usb-belyi-1874606/properties/"
r = requests.get(url, headers=H, timeout=15)
soup = BeautifulSoup(r.text, "html.parser")

# Ищем элементы с классом содержащим ProductPropertiesItem
items = soup.find_all(class_=re.compile(r'ProductPropertiesItem'))
print(f"ProductPropertiesItem: {len(items)}")
for item in items[:5]:
    name_el = item.find(class_=re.compile(r'ProductPropertiesName'))
    val_el  = item.find(class_=re.compile(r'ProductPropertiesValue'))
    name = name_el.get_text(strip=True) if name_el else '?'
    val  = val_el.get_text(strip=True)  if val_el  else '?'
    print(f"  {name!r}: {val!r}")

# Все пары
print(f"\nВсе пары:")
pairs = {}
for item in items:
    name_el = item.find(class_=re.compile(r'ProductPropertiesName'))
    val_el  = item.find(class_=re.compile(r'ProductPropertiesValue'))
    if name_el and val_el:
        name = name_el.get_text(strip=True)
        val  = val_el.get_text(strip=True)
        pairs[name] = val
        print(f"  {name!r}: {val!r}")

# Цена
price_el = soup.find(class_=re.compile(r'Price__price'))
print(f"\nЦена: {price_el.get_text(strip=True) if price_el else 'не найдена'!r}")

# Название и бренд
title_el = soup.find('h1')
print(f"Заголовок: {title_el.get_text(strip=True)[:80] if title_el else '?'!r}")

# Ссылка на продукт (каноническая)
canonical = soup.find('link', rel='canonical')
print(f"Canonical URL: {canonical['href'] if canonical else '?'!r}")
