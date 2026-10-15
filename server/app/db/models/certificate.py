import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, UUIDPrimaryKeyMixin


class Certificate(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "certificates"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_certificate_student_course"),
    )

    certificate_code: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    final_percentage: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_by: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    pdf_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    student: Mapped["User"] = relationship("User", back_populates="certificates", foreign_keys=[student_id])
    course: Mapped["Course"] = relationship("Course", back_populates="certificates")
    revoker: Mapped[Optional["User"]] = relationship("User", foreign_keys=[revoked_by])
