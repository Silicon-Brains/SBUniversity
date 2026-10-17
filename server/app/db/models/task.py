import enum
import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class TaskType(str, enum.Enum):
    EXAM = "exam"
    ASSIGNMENT = "assignment"


class TaskVerification(str, enum.Enum):
    AUTO = "auto"
    TEACHER_APPROVAL = "teacher_approval"


class TaskStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class TaskResourceType(str, enum.Enum):
    VIDEO = "video"
    LEARNING_SOURCE = "learning_source"


class TaskAssignmentScope(str, enum.Enum):
    ALL_STUDENTS = "all_students"
    SELECTED_STUDENTS = "selected_students"


class CompletionStatus(str, enum.Enum):
    PENDING_REVIEW = "pending_review"
    COMPLETED = "completed"
    REJECTED = "rejected"
    REVOKED = "revoked"


class Task(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint("points >= 0", name="ck_task_points_positive"),
        CheckConstraint(
            "(resource_type IS NULL AND resource_url IS NULL) OR "
            "(resource_type IS NOT NULL AND resource_url IS NOT NULL)",
            name="ck_task_resource_type_url",
        ),
        CheckConstraint(
            "(type = 'exam' AND exam_id IS NOT NULL AND verification = 'auto') OR "
            "(type = 'assignment' AND exam_id IS NULL AND "
            "verification IN ('auto', 'teacher_approval'))",
            name="ck_task_type_verification",
        ),
    )

    course_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    type: Mapped[TaskType] = mapped_column(
        Enum(TaskType, name="task_type", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    exam_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("exams.id", ondelete="RESTRICT"), unique=True, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    verification: Mapped[TaskVerification] = mapped_column(
        Enum(TaskVerification, name="task_verification", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
    )
    due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    resource_type: Mapped[Optional[TaskResourceType]] = mapped_column(
        Enum(TaskResourceType, name="task_resource_type", values_callable=lambda obj: [e.value for e in obj]),
        nullable=True,
    )
    resource_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    assignment_scope: Mapped[TaskAssignmentScope] = mapped_column(
        Enum(TaskAssignmentScope, name="task_assignment_scope", values_callable=lambda obj: [e.value for e in obj]),
        default=TaskAssignmentScope.ALL_STUDENTS,
        nullable=False,
    )
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status", values_callable=lambda obj: [e.value for e in obj]),
        default=TaskStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    course: Mapped["Course"] = relationship("Course", back_populates="tasks")
    creator: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by])
    exam: Mapped[Optional["Exam"]] = relationship("Exam", back_populates="task", foreign_keys=[exam_id])
    completions: Mapped[List["TaskCompletion"]] = relationship("TaskCompletion", back_populates="task", cascade="all, delete-orphan")
    recipients: Mapped[List["TaskRecipient"]] = relationship("TaskRecipient", back_populates="task", cascade="all, delete-orphan")


class TaskRecipient(Base):
    __tablename__ = "task_recipients"

    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    task: Mapped["Task"] = relationship("Task", back_populates="recipients")


class TaskCompletion(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "task_completions"
    __table_args__ = (
        UniqueConstraint("task_id", "student_id", name="uq_task_student_completion"),
        CheckConstraint("points_awarded >= 0", name="ck_completion_points_positive"),
        CheckConstraint(
            "(status = 'completed' AND completed_at IS NOT NULL) OR (status != 'completed')",
            name="ck_completion_completed_at",
        ),
    )

    task_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("tasks.id", ondelete="RESTRICT"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[CompletionStatus] = mapped_column(
        Enum(CompletionStatus, name="completion_status", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        index=True,
    )
    submission_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submission_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    points_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    reviewed_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    revoked_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    task: Mapped["Task"] = relationship("Task", back_populates="completions")
    student: Mapped["User"] = relationship("User", back_populates="task_completions", foreign_keys=[student_id])
    reviewer: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reviewed_by])
    revoker: Mapped[Optional["User"]] = relationship("User", foreign_keys=[revoked_by])


class TaskVideoProgress(Base):
    __tablename__ = "task_video_progress"
    __table_args__ = (
        CheckConstraint(
            "progress_percent >= 0 AND progress_percent <= 100",
            name="ck_task_video_progress_percent",
        ),
    )

    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    progress_percent: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    task: Mapped["Task"] = relationship("Task")
    student: Mapped["User"] = relationship("User")
