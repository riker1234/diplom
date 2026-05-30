from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class RecommendRequest(BaseModel):
    category: str
    answers: dict[str, str | int | float]


class ScoreBreakdownItem(BaseModel):
    label: str
    points: int
    positive: bool


class RecommendResultItem(BaseModel):
    id: int
    name: str
    brand: Optional[str] = None
    price: Optional[float] = None
    wb_price: Optional[float] = None
    citilink_price: Optional[float] = None
    best_price: Optional[float] = None
    score: int
    score_breakdown: list[ScoreBreakdownItem] = []
    image_url: Optional[str] = None
    ozon_url: Optional[str] = None
    dns_url: Optional[str] = None
    wb_url: Optional[str] = None
    citilink_url: Optional[str] = None
    updated_at: Optional[datetime] = None
    # Mouse
    sensor: Optional[str] = None
    weight_g: Optional[float] = None
    max_dpi: Optional[int] = None
    button_count: Optional[int] = None
    connection_types: Optional[str] = None
    has_rgb: Optional[bool] = None
    color: Optional[str] = None
    # Keyboard
    keyboard_type: Optional[str] = None
    switches: Optional[str] = None
    form_factor: Optional[str] = None
    key_count: Optional[int] = None
    layout: Optional[str] = None
    keycap_material: Optional[str] = None
    keycap_manufacturing: Optional[str] = None
    # Monitor
    diagonal_inch: Optional[float] = None
    resolution: Optional[str] = None
    refresh_rate_hz: Optional[int] = None
    matrix_type: Optional[str] = None
    response_time_ms: Optional[float] = None
    # Headphones
    construction_type: Optional[str] = None
    has_microphone: Optional[bool] = None
    impedance_ohm: Optional[int] = None
    frequency_response: Optional[str] = None
    # Microphone
    mic_type: Optional[str] = None
    directionality: Optional[str] = None
    frequency_range: Optional[str] = None
    # Mousepad
    size: Optional[str] = None
    surface_material: Optional[str] = None
    thickness_mm: Optional[float] = None

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
