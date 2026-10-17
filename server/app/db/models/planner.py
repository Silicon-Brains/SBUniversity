import enum
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class PlannerEntryKind(str, enum.Enum):
    LEARNING_PLAN = "learning_plan"
    NOTE = "note"
    STICKY_NOTE = "sticky_note"
    EVENT = "event"
    VOICE_NOTE = "voice_note"


class PlannerNoteShape(str, enum.Enum):
    RECTANGLE = "rectangle"
    ROUNDED = "rounded"
    CIRCLE = "circle"
    CLOUD = "cloud"
    STAR = "star"


class PlannerEntry(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "planner_entries"
    __table_args__ = (
        CheckConstraint(
            "audio_size_bytes IS NULL OR (audio_size_bytes > 0 AND audio_size_bytes <= 26214400)",
            name="ck_planner_entry_audio_size",
        ),
        CheckConstraint(
            "(kind = 'voice_note' AND audio_path IS NOT NULL AND audio_mime_type IS NOT NULL "
            "AND audio_size_bytes IS NOT NULL) OR "
            "(kind != 'voice_note' AND audio_path IS NULL AND audio_mime_type IS NULL "
            "AND audio_size_bytes IS NULL)",
            name="ck_planner_entry_audio_fields",
        ),
        CheckConstraint(
            "length(color) = 7 AND substr(color, 1, 1) = '#'",
            name="ck_planner_entry_color",
        ),
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[PlannerEntryKind] = mapped_column(
        Enum(
            PlannerEntryKind,
            name="planner_entry_kind",
            values_callable=lambda obj: [entry.value for entry in obj],
        ),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    color: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        default="#fef3c7",
        server_default="#fef3c7",
    )
    shape: Mapped[PlannerNoteShape] = mapped_column(
        Enum(
            PlannerNoteShape,
            name="planner_note_shape",
            values_callable=lambda obj: [entry.value for entry in obj],
        ),
        nullable=False,
        default=PlannerNoteShape.ROUNDED,
        server_default="rounded",
    )
    emoji: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    audio_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    audio_mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    audio_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
