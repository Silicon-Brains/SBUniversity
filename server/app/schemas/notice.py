import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.db.models.notice import NoticeAudience, NoticePriority, NoticeStatus


class NoticeCreate(BaseModel):
    title: str
    body: str
    audience: NoticeAudience = NoticeAudience.ALL
    course_id: Optional[uuid.UUID] = None
    priority: NoticePriority = NoticePriority.NORMAL
    is_pinned: bool = False
    expires_at: Optional[datetime] = None


class NoticeUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None
    priority: Optional[NoticePriority] = None
    is_pinned: Optional[bool] = None
    status: Optional[NoticeStatus] = None
    expires_at: Optional[datetime] = None


class NoticeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    author_id: uuid.UUID
    author_name: Optional[str] = None
    title: str
    body: str
    audience: NoticeAudience
    course_id: Optional[uuid.UUID] = None
    course_title: Optional[str] = None
    priority: NoticePriority
    is_pinned: bool
    status: NoticeStatus
    published_at: datetime
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
