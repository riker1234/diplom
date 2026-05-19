import sys, time, requests
sys.stdout.reconfigure(encoding='utf-8')
import os; os.chdir(r'C:\Users\User\Desktop\diplom\backend')
from app.parsers.wildberries import _browser_search, _get_basket, _DETAIL_HEADERS

def fetch_card(pid):
    vol = pid // 100000
    part = pid // 1000
    basket = _get_basket(vol)
    url = f'https://basket-{basket}.wbbasket.ru/vol{vol}/part{part}/{pid}/info/ru/card.json'
    r = requests.get(url, headers=_DETAIL_HEADERS, timeout=10)
    if r.status_code == 200:
        return r.json()
    return {}

def probe(category, query):
    print(f'\n=== {category.upper()} ({query!r}) ===')
    products = _browser_search(query, 3)
    for p in products[:2]:
        pid = p['id']
        card = fetch_card(pid)
        opts = card.get('options', [])
        if not opts:
            for g in card.get('grouped_params', []):
                opts.extend(g.get('params', []))
        name = p.get('name', '')
        print(f'  [{pid}] {name[:50]}')
        for o in opts:
            print(f'    {o.get("name","")!r}: {str(o.get("value",""))[:50]!r}')
        time.sleep(0.5)

probe('наушники', 'игровые наушники гарнитура')
probe('коврики', 'игровой коврик для мыши xl')
