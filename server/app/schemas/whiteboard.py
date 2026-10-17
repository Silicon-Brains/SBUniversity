import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.models.user import UserRole

WhiteboardTool = Literal["pen", "eraser", "line", "rectangle", "ellipse"]


class WhiteboardCourseResponse(BaseModel):
    id: uuid.UUID
    code: str
    title: str
    is_live: bool


class WhiteboardPoint(BaseModel):
    x: float = Field(ge=0, le=1)
    y: float = Field(ge=0, le=1)


class WhiteboardStrokeCreate(BaseModel):
    tool: WhiteboardTool
    color: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    width: int = Field(ge=1, le=40)
    points: list[WhiteboardPoint] = Field(min_length=2, max_length=500)


class WhiteboardStrokeResponse(WhiteboardStrokeCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    author_id: uuid.UUID
    created_at: datetime


class WhiteboardSessionResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    created_by: uuid.UUID | None = None
    is_active: bool
    board_generation: int
    started_at: datetime
    ended_at: datetime | None
    strokes: list[WhiteboardStrokeResponse]
    strokes_are_snapshot: bool = True


class WhiteboardMessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=1000)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message cannot be empty")
        return value


class WhiteboardMessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    sender_id: uuid.UUID
    sender_name: str
    sender_role: UserRole
    is_mine: bool
    content: str
    created_at: datetime
    expires_at: datetime
