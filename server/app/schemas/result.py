import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.exam import QuestionResponse


class PerQuestionReview(BaseModel):
    question_id: uuid.UUID
    question_text: str
    marks: float
    explanation: Optional[str] = None
    selected_option_id: Optional[uuid.UUID] = None
    correct_option_id: Optional[uuid.UUID] = None
    is_correct: bool
    options: List[dict]


class ResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    attempt_id: uuid.UUID
    exam_id: uuid.UUID
    student_id: uuid.UUID
    score: float
    total_marks: float
    percentage: float
    grade: str
    passed: bool
    time_taken_sec: int
    rank_in_exam: Optional[int] = None
    pdf_path: Optional[str] = None
    created_at: datetime


class ResultDetailResponse(ResultResponse):
    exam_title: str
    course_title: str
    student_name: str
    reviews: Optional[List[PerQuestionReview]] = None
