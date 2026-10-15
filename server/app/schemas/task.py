import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.db.models.task import CompletionStatus, TaskStatus, TaskType, TaskVerification


class TaskCreate(BaseModel):
    course_id: uuid.UUID
    title: str
    description: Optional[str] = None
    points: int = Field(ge=0)
    due_at: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_at: Optional[datetime] = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    course_id: uuid.UUID
    course_title: Optional[str] = None
    created_by: uuid.UUID
    type: TaskType
    exam_id: Optional[uuid.UUID] = None
    title: str
    description: Optional[str] = None
    points: int
    verification: TaskVerification
    due_at: Optional[datetime] = None
    status: TaskStatus
    created_at: datetime
    # Student view augmentation
    my_completion_id: Optional[uuid.UUID] = None
    my_status: Optional[CompletionStatus] = None
    points_earned: Optional[int] = None


class TaskCompleteRequest(BaseModel):
    note: Optional[str] = None
    url: Optional[str] = None


class TaskCompletionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    task_id: uuid.UUID
    task_title: Optional[str] = None
    course_id: Optional[uuid.UUID] = None
    course_title: Optional[str] = None
    student_id: uuid.UUID
    student_name: Optional[str] = None
    status: CompletionStatus
    submission_note: Optional[str] = None
    submission_url: Optional[str] = None
    points_awarded: int
    submitted_at: datetime
    completed_at: Optional[datetime] = None
    reviewed_by: Optional[uuid.UUID] = None
    reviewed_at: Optional[datetime] = None
    review_note: Optional[str] = None


class TaskReviewRequest(BaseModel):
    review_note: Optional[str] = None


class TaskPointsHistoryItem(BaseModel):
    completion_id: uuid.UUID
    task_id: uuid.UUID
    task_title: str
    course_title: str
    points: int
    completed_at: datetime


class StudentPointsResponse(BaseModel):
    total_points: int
    tasks_completed: int
    rank: Optional[int] = None
    history: List[TaskPointsHistoryItem] = []
