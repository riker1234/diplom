"""Смотрим полные CDN данные для проблемного продукта."""
import sys, requests
sys.stdout.reconfigure(encoding='utf-8')

H = {"User-Agent": "Mozilla/5.0 Chrome/124.0.0.0", "Referer": "https://www.wildberries.ru/"}

def get_basket(vol):
    ranges = [(143,"01"),(287,"02"),(431,"03"),(719,"04"),(1007,"05"),(1061,"06"),
        (1115,"07"),(1169,"08"),(1313,"09"),(1601,"10"),(1655,"11"),(1919,"12"),
        (2045,"13"),(2189,"14"),(2405,"15"),(2621,"16"),(2837,"17"),(3053,"18"),
        (3269,"19"),(3485,"20"),(3701,"21"),(3917,"22"),(4133,"23"),(4349,"24")]
    for mv, b in ranges:
        if vol <= mv: return b
    return "25"

# G102 проводная (dpi=7 - подозрительно)
pid = 160842183
vol = pid // 100000
part = pid // 1000
basket = get_basket(vol)
url = f"https://basket-{basket}.wbbasket.ru/vol{vol}/part{part}/{pid}/info/ru/card.json"
r = requests.get(url, headers=H, timeout=10)
print(f"G102 Проводная (id={pid}): basket={basket}, status={r.status_code}")
if r.status_code == 200:
    opts = r.json().get("options", [])
    print(f"Всего опций: {len(opts)}")
    for o in opts:
        name = o.get('name','')
        val = o.get('value','')
        # Выделяем поля связанные с DPI / разрешением
        if any(k in name.lower() for k in ['dpi', 'разрешен', 'сенсор']):
            print(f"  >> {name!r}: {val!r}")
        else:
            print(f"     {name!r}: {val!r}")
