# Ozon Parser — Design Spec

**Date:** 2026-05-17

## Goal

Replace the Wildberries parser with an Ozon parser across all 6 peripheral categories (mice, keyboards, monitors, headphones, microphones, mousepads). Remove all WB-specific and DNS-specific fields from models. Clear existing product data and repopulate from Ozon.

## Out of Scope

- DNS parser (planned for later, will be added via a separate migration)
- Frontend changes
- Recommendation logic changes

---

## 1. Model Changes

All 6 models (`Mouse`, `Keyboard`, `Monitor`, `Headphones`, `Microphone`, `Mousepad`) get the following field replacements:

**Remove:**
- `wb_sku`
- `wb_url`
- `dns_product_id`
- `dns_url`

**Add:**
- `ozon_sku = Column(String, unique=True, nullable=True)`
- `ozon_url = Column(String, nullable=True)`

All other fields (characteristics, `price`, `image_url`, `brand`, `name`) remain unchanged.

**Migration:** One Alembic migration drops the old columns and adds the new ones. All existing rows are deleted before migration (truncate or drop+recreate).

---

## 2. Ozon Parser (`backend/app/parsers/ozon.py`)

### Data Source

Ozon is a React SPA. Product data is served via an internal JSON API:

- **Search / product list:**
  `GET https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2?url=/category/{slug}/?{params}`
  Returns a JSON tree; products are inside `widgetStates` → component with `"name": "searchResultsV2"` → `"items"`.

- **Product characteristics:**
  `GET https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2?url=/product/{slug}-{ozon_id}/`
  Returns characteristics inside `widgetStates` → component with `"name": "webCharacteristics"` → `"characteristics"` — a list of groups, each with `"short_characteristics"` list of `{"name": ..., "values": [{"text": ...}]}`.

Required headers:
```
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...
x-o3-app-name: ozonweb
x-o3-app-version: 5.0.0
Accept: application/json
```

No cookies or auth required for basic product data.

### Structure

Mirrors `wildberries.py` exactly:

```
_parse_float / _parse_int / _parse_bool   — same helpers
_MOUSE_KEYS, _KEYBOARD_KEYS, ...           — Russian field name sets for Ozon labels
_map_options(options, keys_map)            — generic mapper
_map_mouse / _map_keyboard / ...           — per-category mappers
_search_ozon(query, limit)                 — fetch product list via entrypoint API
_fetch_details(product_ids)               — fetch characteristics per product
_run_parse(db, query, model_class, mapper) — upsert loop
parse_mice / parse_keyboards / ...         — public entry points
backfill_mice / backfill_keyboards / ...   — backfill existing records with null chars
```

### Field Mapping

Ozon uses Russian labels similar to WB but with some differences. Key mappings to verify during implementation (from Ozon product pages):

| Category  | Ozon field name (approximate) | Model field |
|-----------|-------------------------------|-------------|
| Mouse     | Тип сенсора                   | sensor |
| Mouse     | Тип подключения               | connection_types |
| Mouse     | Вес                           | weight_g |
| Mouse     | Тип переключателей            | switches |
| Keyboard  | Тип переключателей            | switches |
| Keyboard  | Форм-фактор                   | form_factor |
| Monitor   | Частота обновления экрана     | refresh_rate_hz |
| Monitor   | Диагональ экрана              | diagonal_inch |
| Monitor   | Тип матрицы                   | matrix_type |
| Monitor   | Разрешение экрана             | resolution |
| Headphones| Наличие микрофона             | has_microphone |
| Headphones| Тип подключения               | connection_types |
| Microphone| Тип микрофона                 | mic_type |
| Mousepad  | Подсветка                     | has_rgb |
| Mousepad  | Жёсткость                     | hardness |

**Note:** Exact field names must be verified by fetching a real Ozon product page during implementation and printing all characteristic names.

### Image URL

Ozon provides image URLs directly in the product list JSON (`images` or `coverImage` field). No construction needed.

---

## 3. Admin Router Changes (`backend/app/routers/admin.py`)

Replace all WB imports and endpoints with Ozon equivalents:
- `/admin/parse/{category}` → calls `parse_{category}(db)` from `ozon.py`
- `/admin/backfill/{category}` → calls `backfill_{category}(db)` from `ozon.py`

Remove `wildberries.py` imports entirely.

---

## 4. Data Migration Plan

1. Run Alembic migration (drops WB/DNS columns, adds `ozon_sku`/`ozon_url`)
2. Truncate all 6 product tables (data is stale WB data, no longer valid)
3. Run Ozon parsers for all 6 categories via admin API

---

## 5. Files Changed

| File | Action |
|------|--------|
| `app/models/mouse.py` | Remove wb_sku, wb_url, dns_*; add ozon_sku, ozon_url |
| `app/models/keyboard.py` | Same |
| `app/models/monitor.py` | Same |
| `app/models/headphones.py` | Same |
| `app/models/microphone.py` | Same |
| `app/models/mousepad.py` | Same |
| `app/parsers/wildberries.py` | Delete |
| `app/parsers/ozon.py` | Create |
| `app/routers/admin.py` | Swap WB → Ozon imports and endpoints |
| `alembic/versions/XXXX_ozon.py` | New migration |
| `tests/test_wildberries_parser.py` | Replace with `test_ozon_parser.py` |

---

## 6. Testing

Unit tests mirror current `test_wildberries_parser.py`:
- `_parse_float`, `_parse_int`, `_parse_bool`
- All 6 `_map_*` functions with sample Ozon characteristic dicts
- `_fetch_details` with mocked `requests.get`
- `parse_mice` integration: mock `_search_ozon` + `_fetch_details`, verify DB upsert
