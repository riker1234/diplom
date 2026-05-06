from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.recommendation.questions import get_questions, SUPPORTED_CATEGORIES
from app.recommendation.engine import recommend
from app.schemas.recommendation import (
    RecommendRequest,
    RecommendResponse,
    QuestionsResponse,
)

router = APIRouter(prefix="/recommend", tags=["recommendation"])


@router.get("/questions/{category}", response_model=QuestionsResponse)
def get_category_questions(category: str):
    if category not in SUPPORTED_CATEGORIES:
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")
    return {"category": category, "questions": get_questions(category)}


@router.post("/", response_model=RecommendResponse)
def recommend_products(request: RecommendRequest, db: Session = Depends(get_db)):
    if request.category not in SUPPORTED_CATEGORIES:
        raise HTTPException(status_code=404, detail=f"Category '{request.category}' not found")
    results = recommend(request.category, request.answers, db)
    return {"category": request.category, "total": len(results), "results": results}
