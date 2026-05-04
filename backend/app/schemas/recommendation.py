from pydantic import BaseModel
from typing import Dict, List

class QuestionOption(BaseModel):
    value: str
    label: str

class Question(BaseModel):
    id: str
    text: str
    options: List[QuestionOption]

class RecommendationRequest(BaseModel):
    category: str
    answers: Dict[str, str]

class StoreInfo(BaseModel):
    store_name: str
    store_address: str
    city: str
    in_stock: bool
