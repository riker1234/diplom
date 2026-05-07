from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.parsers.wildberries import parse_mice

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(x_admin_key: str = Header(...)):
    """Проверяет, что в заголовке X-Admin-Key передан правильный ключ."""
    if x_admin_key != settings.ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post(
    "/parse/mice",
    summary="Запустить парсинг мышей с Wildberries",
    dependencies=[Depends(_require_admin)],
)
def trigger_parse_mice(db: Session = Depends(get_db)):
    result = parse_mice(db)
    return result
