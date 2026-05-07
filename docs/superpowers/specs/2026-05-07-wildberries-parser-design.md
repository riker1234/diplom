# Wildberries Parser — Design Spec

**Date:** 2026-05-07  
**Module:** `app/parsers/wildberries.py`, `app/routers/admin.py`  
**Status:** Approved, ready for implementation

---

## Context

The recommendation engine is complete but the database is empty. We need real product data to make the engine useful. This module fetches mouse products from Wildberries using their public API (no auth required) and saves them to the `mice` table.

Existing codebase: FastAPI + SQLAlchemy + PostgreSQL. Models already defined. `.env` already exists but needs `ADMIN_KEY` added.

---

## Scope

**In scope:** Mouse category only (keyboard and monitor added later by extending the same pattern)  
**Out of scope:** DNS parser, APScheduler background jobs, other categories

---

## Architecture

Two new files + registration in `main.py`:

```
app/
├── parsers/
│   └── wildberries.py    ← API client + characteristic mapper + upsert logic
└── routers/
    └── admin.py          ← single protected endpoint to trigger parsing
```

Data flow:
```
POST /admin/parse/wildberries/mouse  (X-Admin-Key header required)
    → fetch product list from WB Search API (query: "игровая мышь")
    → extract product IDs + basic fields (name, brand, price)
    → batch fetch characteristics from WB Detail API
    → map characteristic names to model fields
    → upsert into mice table (update if wb_sku exists, insert if new)
    → return {"added": N, "updated": N, "failed": N}
```

---

## Wildberries API

### Search API

```
GET https://search.wb.ru/exactmatch/ru/common/v5/search
    ?query=игровая+мышь
    &resultset=catalog
    &limit=100
    &dest=-1257786
```

Response structure:
```json
{
  "data": {
    "products": [
      {
        "id": 12345678,
        "name": "Игровая мышь Logitech G102",
        "brand": "Logitech",
        "priceU": 199000
      }
    ]
  }
}
```

Price: `priceU / 100` = рубли.

### Detail API

```
GET https://card.wb.ru/cards/v1/detail
    ?appType=1&curr=rub&dest=-1257786
    &nm=id1;id2;id3;...
```

Up to 100 IDs per request. Response:
```json
{
  "data": {
    "products": [
      {
        "id": 12345678,
        "options": [
          {"name": "Вес", "value": "95 г"},
          {"name": "Тип подключения", "value": "USB"}
        ]
      }
    ]
  }
}
```

---

## Characteristic Mapping (Mouse)

| DB field | WB characteristic names to search |
|---|---|
| `weight_g` | «Вес», «Масса» |
| `connection_types` | «Тип подключения», «Интерфейс» |
| `sensor` | «Сенсор», «Тип сенсора» |
| `switches` | «Переключатели», «Микровыключатели» |

Weight parsing: strip non-numeric characters, convert to float. Example: `"95 г"` → `95.0`

If a characteristic is not found → field stays `None`. This is expected — not all products have all specs.

---

## Other Fields

| DB field | Source |
|---|---|
| `name` | Search API `name` |
| `brand` | Search API `brand` |
| `price` | Search API `priceU / 100` |
| `wb_sku` | Search API `id` as string |
| `wb_url` | `https://www.wildberries.ru/catalog/{id}/detail.aspx` |
| `image_url` | Constructed: `https://basket-{basket}.wbbasket.ru/vol{vol}/part{part}/{id}/images/big/1.webp` |

Image URL basket calculation:
```python
vol = id // 100000
part = id // 1000

def get_basket(vol: int) -> str:
    thresholds = [143,287,431,719,1007,1061,1115,1169,1313,1601,
                  1655,1919,2045,2189,2405,2621,2837,3053,3269,3485,
                  3701,3917,4133,4349]
    for i, t in enumerate(thresholds):
        if vol <= t:
            return str(i + 1).zfill(2)
    return "25"
```

---

## Upsert Logic

```
For each product from WB:
    Find existing record WHERE wb_sku = product.wb_sku
    If found  → UPDATE price, image_url, updated_at
    If not found → INSERT new record
    If error → increment failed counter, continue
```

Returns: `{"added": N, "updated": N, "failed": N}`

---

## Admin Endpoint

### POST `/admin/parse/wildberries/mouse`

**Headers:** `X-Admin-Key: <value from .env ADMIN_KEY>`

**Response 200:**
```json
{"added": 47, "updated": 12, "failed": 3}
```

**Response 403:** wrong or missing admin key.

**`.env` addition required:**
```
ADMIN_KEY=diplom2026
```

**`config.py` addition required:**
```python
ADMIN_KEY: str = "diplom2026"
```

---

## Error Handling

- WB API unreachable → raise HTTPException 503
- Individual product parse fails → skip, increment `failed`, continue
- DB error on upsert → skip, increment `failed`, continue

---

## Testing

- Unit test: characteristic mapper extracts `weight_g` from `"95 г"` → `95.0`
- Unit test: mapper returns `None` for unknown characteristic name
- Unit test: `wb_url` constructed correctly from product ID
- Integration test: `POST /admin/parse/wildberries/mouse` without key → 403
- Integration test: `POST /admin/parse/wildberries/mouse` with wrong key → 403
- WB API calls are mocked in tests (no real network calls)
