"""Persist student watch progress for video tasks.

Revision ID: 005_task_video_progress
Revises: 004_fix_task_type_check_constraint
Create Date: 2026-10-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "005_task_video_progress"
down_revision = "004_fix_task_type_check_constraint"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "task_video_progress",
        sa.Column(
            "task_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tasks.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("progress_percent", sa.Float(), nullable=False, server_default="0"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "progress_percent >= 0 AND progress_percent <= 100",
            name="ck_task_video_progress_percent",
        ),
    )
    op.create_index(
        "ix_task_video_progress_student_id",
        "task_video_progress",
        ["student_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_task_video_progress_student_id", table_name="task_video_progress")
    op.drop_table("task_video_progress")
