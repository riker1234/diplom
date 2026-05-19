import sys, json, time
sys.stdout.reconfigure(encoding='utf-8')
import app.parsers.ozon as oz

driver = oz._get_driver()
time.sleep(1)

products = oz._search_ozon('игровая мышь', 1)
if not products:
    print("NO PRODUCTS"); sys.exit(1)

p = products[0]
url = oz._get_url(p)
features_url = url.rstrip('/') + '/features/'
api_url = f"/api/entrypoint-api.bx/page/json/v2?url={features_url}"
data = oz._browser_get(api_url)
if not data:
    print("No data"); sys.exit(1)

ws = data.get("widgetStates", {})
print(f"Total widgets: {len(ws)}")

# Print ALL webCharacteristics widgets
for k in ws.keys():
    if "webCharacteristics" in k:
        print(f"\n=== {k} ===")
        try:
            w = json.loads(ws[k]) if isinstance(ws[k], str) else ws[k]
            chars = w.get("characteristics", [])
            print(f"  characteristics groups: {len(chars)}")
            for g_i, group in enumerate(chars):
                print(f"  group[{g_i}] keys: {list(group.keys())}")
                for key in ("short", "full", "items", "list"):
                    items = group.get(key, [])
                    if items:
                        print(f"    [{key}] ({len(items)} items):")
                        for item in items[:20]:
                            name = item.get("name", "")
                            vals = item.get("values", [])
                            val = "; ".join(v.get("text","") for v in vals)
                            print(f"      '{name}' = '{val}'")
        except Exception as e:
            print(f"  error: {e}")
