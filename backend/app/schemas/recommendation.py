from pydantic import BaseModel
from typing import Optional


class RecommendRequest(BaseModel):
    category: str
    answers: dict[str, str | int | float]


class RecommendResultItem(BaseModel):
    id: int
    name: str
    brand: Optional[str] = None
    price: Optional[float] = None
    wb_price: Optional[float] = None
    citilink_price: Optional[float] = None
    best_price: Optional[float] = None
    score: int
    image_url: Optional[str] = None
    ozon_url: Optional[str] = None
    dns_url: Optional[str] = None
    wb_url: Optional[str] = None
    citilink_url: Optional[str] = None

    model_config = {"from_attributes": True}


class RecommendResponse(BaseModel):
    category: str
    total: int
    results: list[RecommendResultItem]


class QuestionOption(BaseModel):
    value: str
    label: str


class Question(BaseModel):
    id: str
    text: str
    type: str
    options: Optional[list[QuestionOption]] = None
    placeholder: Optional[str] = None


class QuestionsResponse(BaseModel):
    category: str
    questions: list[Question]
