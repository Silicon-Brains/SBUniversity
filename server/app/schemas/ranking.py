import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class RankedStudentItem(BaseModel):
    rank: int
    student_id: uuid.UUID
    name: str
    avatar_url: Optional[str] = None
    points: int
    tasks_completed: int


class LeaderboardResponse(BaseModel):
    updated_at: datetime
    scope: str = "overall"
    course_id: Optional[uuid.UUID] = None
    items: List[RankedStudentItem]


class MyRankResponse(BaseModel):
    student_id: uuid.UUID
    rank: Optional[int] = None
    points: int
    tasks_completed: int
