import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class WhiteboardSession(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "whiteboard_sessions"
    __table_args__ = (
        Index(
            "uq_whiteboard_sessions_active_course",
            "course_id",
            unique=True,
            postgresql_where=text("is_active = true"),
            sqlite_where=text("is_active = 1"),
        ),
    )

    course_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    board_generation: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    strokes: Mapped[list["WhiteboardStroke"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="WhiteboardStroke.created_at",
    )
    messages: Mapped[list["WhiteboardMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="WhiteboardMessage.created_at",
    )


class WhiteboardStroke(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "whiteboard_strokes"
    __table_args__ = (
        CheckConstraint(
            "tool IN ('pen', 'eraser', 'line', 'rectangle', 'ellipse')",
            name="ck_whiteboard_stroke_tool",
        ),
        CheckConstraint("width BETWEEN 1 AND 40", name="ck_whiteboard_stroke_width"),
        CheckConstraint(
            "length(color) = 7 AND substr(color, 1, 1) = '#'",
            name="ck_whiteboard_stroke_color",
        ),
        Index("ix_whiteboard_strokes_session_created", "session_id", "created_at"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("whiteboard_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tool: Mapped[str] = mapped_column(String(16), nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    points: Mapped[list[dict[str, float]]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    session: Mapped[WhiteboardSession] = relationship(back_populates="strokes")


class WhiteboardMessage(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "whiteboard_messages"
    __table_args__ = (
        CheckConstraint(
            "length(content) > 0 AND length(content) <= 1000",
            name="ck_whiteboard_message_content_length",
        ),
        CheckConstraint(
            "expires_at > created_at",
            name="ck_whiteboard_message_expiry",
        ),
        Index(
            "ix_whiteboard_messages_session_created",
            "session_id",
            "created_at",
        ),
        Index("ix_whiteboard_messages_expires_at", "expires_at"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("whiteboard_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    session: Mapped[WhiteboardSession] = relationship(back_populates="messages")
