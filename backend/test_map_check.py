import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
os.environ.setdefault('DATABASE_URL', 'sqlite:///./test.db')

import requests
from app.parsers.wildberries import _map_mouse, _fetch_details, _build_card_json_url

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Referer': 'https://www.wildberries.ru/',
}

pid = 335655717
url = _build_card_json_url(pid)
print(f'URL: {url}')

r = requests.get(url, headers=HEADERS, timeout=10)
print(f'Status: {r.status_code}')

data = r.json()
options = data.get('options', [])
print(f'\nПолей в options: {len(options)}')
for o in options:
    print(f'  "{o.get("name")}" -> "{o.get("value")}"')

print('\n--- _map_mouse результат ---')
result = _map_mouse(options)
for k, v in result.items():
    print(f'  {k}: {repr(v)}')

# Также проверим через _fetch_details
print('\n--- _fetch_details результат ---')
details = _fetch_details([pid])
if pid in details:
    print(f'Полей: {len(details[pid])}')
    mapped = _map_mouse(details[pid])
    for k, v in mapped.items():
        print(f'  {k}: {repr(v)}')
else:
    print('pid не найден в details!')
