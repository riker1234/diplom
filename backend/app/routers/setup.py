from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.recommendation.setup_engine import recommend_setup

router = APIRouter(prefix="/recommend/setup", tags=["setup"])


class SetupRequest(BaseModel):
    total_budget: float
    use_case: str = "both"   # gaming | work | both
    priority: str = "balance"  # budget | balance | flagship


@router.post("")
def get_setup_recommendation(req: SetupRequest, db: Session = Depends(get_db)):
    return recommend_setup(
        total_budget=req.total_budget,
        use_case=req.use_case,
        priority=req.priority,
        db=db,
    )
