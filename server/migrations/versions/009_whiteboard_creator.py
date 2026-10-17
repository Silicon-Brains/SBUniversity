"""Record the user who created a live whiteboard, whether admin or teacher.

Revision ID: 009_whiteboard_creator
Revises: 008_live_whiteboard
Create Date: 2026-10-17
"""
from alembic import op

revision = "009_whiteboard_creator"
down_revision = "008_live_whiteboard"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index(
        "ix_whiteboard_sessions_teacher_id",
        table_name="whiteboard_sessions",
    )
    op.alter_column(
        "whiteboard_sessions",
        "teacher_id",
        new_column_name="created_by",
    )
    op.create_index(
        "ix_whiteboard_sessions_created_by",
        "whiteboard_sessions",
        ["created_by"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_whiteboard_sessions_created_by",
        table_name="whiteboard_sessions",
    )
    op.alter_column(
        "whiteboard_sessions",
        "created_by",
        new_column_name="teacher_id",
    )
    op.create_index(
        "ix_whiteboard_sessions_teacher_id",
        "whiteboard_sessions",
        ["teacher_id"],
    )
