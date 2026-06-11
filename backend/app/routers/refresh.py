"""POST /refresh/{category}/{id} — кнопка «Обновить цену» в карточке товара."""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.mouse import Mouse
from app.models.keyboard import Keyboard
from app.models.monitor import Monitor
from app.models.headphones import Headphones
from app.models.microphone import Microphone
from app.models.mousepad import Mousepad
from app.services import refresh as refresh_service

router = APIRouter(prefix="/refresh", tags=["refresh"])

_MODEL_MAP = {
    "mouse": Mouse,
    "keyboard": Keyboard,
    "monitor": Monitor,
    "headphones": Headphones,
    "microphone": Microphone,
    "mousepad": Mousepad,
}

# Если данные свежее этого окна — не парсим повторно (защита от закликивания)
FRESH_WINDOW = timedelta(minutes=10)


def _payload(p) -> dict:
    return {
        "price": p.price,
        "wb_price": p.wb_price,
        "citilink_price": p.citilink_price,
        "ozon_rating": getattr(p, "ozon_rating", None),
        "ozon_reviews": getattr(p, "ozon_reviews", None),
        "citilink_rating": getattr(p, "citilink_rating", None),
        "citilink_reviews": getattr(p, "citilink_reviews", None),
        "wb_rating": getattr(p, "wb_rating", None),
        "wb_reviews": getattr(p, "wb_reviews", None),
        "updated_at": p.updated_at,
    }


@router.post("/{category}/{product_id}")
def refresh_product(category: str, product_id: int, db: Session = Depends(get_db)):
    model = _MODEL_MAP.get(category)
    if model is None:
        raise HTTPException(status_code=404, detail="Неизвестная категория")

    product = db.get(model, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Товар не найден")

    if product.updated_at is not None and datetime.utcnow() - product.updated_at < FRESH_WINDOW:
        return {"refreshed": False, "message": "Цена уже актуальна", "updated": _payload(product)}

    if not product.ozon_url and not product.citilink_url:
        return {
            "refreshed": False,
            "message": "Для этого товара нет источников с поддержкой обновления",
            "updated": _payload(product),
        }

    try:
        sources = refresh_service.refresh_product(product, db)
    except Exception:
        raise HTTPException(status_code=502, detail="Не удалось обновить данные")

    db.refresh(product)
    ok = any(s in ("ok", "oos") for s in sources.values())
    return {
        "refreshed": ok,
        "sources": sources,
        "message": None if ok else "Источники не ответили — показаны последние данные",
        "updated": _payload(product),
    }
