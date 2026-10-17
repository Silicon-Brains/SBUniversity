import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.db.models.planner import PlannerEntryKind, PlannerNoteShape


class PlannerEntryCreate(BaseModel):
    kind: PlannerEntryKind
    title: str = Field(min_length=1, max_length=160)
    content: Optional[str] = Field(default=None, max_length=20000)
    due_at: Optional[datetime] = None
    color: str = Field(default="#fef3c7", pattern=r"^#[0-9A-Fa-f]{6}$")
    shape: PlannerNoteShape = PlannerNoteShape.ROUNDED
    emoji: Optional[str] = Field(default=None, max_length=16)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Title cannot be empty")
        return normalized


class PlannerEntryUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=160)
    content: Optional[str] = Field(default=None, max_length=20000)
    due_at: Optional[datetime] = None
    is_completed: Optional[bool] = None
    color: Optional[str] = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
    shape: Optional[PlannerNoteShape] = None
    emoji: Optional[str] = Field(default=None, max_length=16)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            raise ValueError("Title cannot be empty")
        normalized = value.strip()
        if not normalized:
            raise ValueError("Title cannot be empty")
        return normalized

    @field_validator("is_completed", "color", "shape", mode="before")
    @classmethod
    def reject_null_for_required_fields(cls, value):
        if value is None:
            raise ValueError("This field cannot be null")
        return value


class PlannerEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    kind: PlannerEntryKind
    title: str
    content: Optional[str]
    due_at: Optional[datetime]
    is_completed: bool
    color: str
    shape: PlannerNoteShape
    emoji: Optional[str]
    audio_mime_type: Optional[str]
    audio_size_bytes: Optional[int]
    audio_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
