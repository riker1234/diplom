import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
os.environ['DATABASE_URL'] = open('.env').read().split('DATABASE_URL=')[1].split()[0]
from app.database import SessionLocal
from app.models.mouse import Mouse
import requests, time

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Referer': 'https://www.wildberries.ru/',
}

def get_basket(vol):
    thresholds = [143,287,431,719,1007,1061,1115,1169,1313,1601,1655,1919,2045,2189,2405,2621,2837,3053,3269,3485,3701,3917,4133,4349]
    for i, t in enumerate(thresholds):
        if vol <= t:
            return str(i+1).zfill(2)
    return '25'

db = SessionLocal()
null_mice = db.query(Mouse).filter(Mouse.sensor == None, Mouse.wb_sku != None).limit(4).all()
for m in null_mice:
    pid = int(m.wb_sku)
    vol = pid // 100000
    part = pid // 1000
    basket = get_basket(vol)
    url = f'https://basket-{basket}.wbbasket.ru/vol{vol}/part{part}/{pid}/info/ru/card.json'
    r = requests.get(url, headers=HEADERS, timeout=10)
    print(f'\n--- {m.name[:50]} (id={pid}), status={r.status_code}')
    if r.status_code == 200:
        opts = r.json().get('options', [])
        for o in opts:
            print(f'  {o.get("name")} -> {o.get("value")}')
    time.sleep(0.5)
db.close()
