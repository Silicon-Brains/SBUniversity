import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDPrimaryKeyMixin


class Result(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "results"

    attempt_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("exam_attempts.id", ondelete="CASCADE"), unique=True, nullable=False)
    exam_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    total_marks: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    grade: Mapped[str] = mapped_column(String, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    time_taken_sec: Mapped[int] = mapped_column(Integer, nullable=False)
    rank_in_exam: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pdf_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    attempt: Mapped["ExamAttempt"] = relationship("ExamAttempt", back_populates="result")
    exam: Mapped["Exam"] = relationship("Exam", back_populates="results")
    student: Mapped["User"] = relationship("User", back_populates="results")
