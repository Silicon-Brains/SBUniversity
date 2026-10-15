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
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class NoticeAudience(str, enum.Enum):
    ALL = "all"
    STUDENTS = "students"
    TEACHERS = "teachers"
    COURSE = "course"


class NoticePriority(str, enum.Enum):
    NORMAL = "normal"
    IMPORTANT = "important"
    URGENT = "urgent"


class NoticeStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Notice(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "notices"
    __table_args__ = (
        CheckConstraint(
            "(audience = 'course' AND course_id IS NOT NULL) OR (audience != 'course')",
            name="ck_notice_course_scope",
        ),
    )

    author_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    audience: Mapped[NoticeAudience] = mapped_column(
        Enum(NoticeAudience, name="notice_audience", values_callable=lambda obj: [e.value for e in obj]),
        default=NoticeAudience.ALL,
        nullable=False,
    )
    course_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("courses.id", ondelete="CASCADE"), nullable=True, index=True)
    priority: Mapped[NoticePriority] = mapped_column(
        Enum(NoticePriority, name="notice_priority", values_callable=lambda obj: [e.value for e in obj]),
        default=NoticePriority.NORMAL,
        nullable=False,
    )
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[NoticeStatus] = mapped_column(
        Enum(NoticeStatus, name="notice_status", values_callable=lambda obj: [e.value for e in obj]),
        default=NoticeStatus.PUBLISHED,
        nullable=False,
        index=True,
    )
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    author: Mapped["User"] = relationship("User", back_populates="notices_authored")
    course: Mapped[Optional["Course"]] = relationship("Course", back_populates="notices")
