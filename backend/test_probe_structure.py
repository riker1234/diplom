import sys, json
sys.stdout.reconfigure(encoding='utf-8')
import app.parsers.ozon as oz

products = oz._search_ozon('игровая мышь', 1)
if not products:
    print("NO PRODUCTS")
    sys.exit(1)

p = products[0]
print("=== KEYS ===")
print(list(p.keys()))

print("\n=== mainState types ===")
for i, s in enumerate(p.get('mainState', [])):
    t = s.get('type')
    content = s.get(t, {})
    print(f"[{i}] type={t}")
    print("    ", json.dumps(content, ensure_ascii=False)[:300])

print("\n=== trackingInfo ===")
print(json.dumps(p.get('trackingInfo', {}), ensure_ascii=False)[:1000])

print("\n=== tileImage ===")
print(json.dumps(p.get('tileImage', {}), ensure_ascii=False)[:300])
