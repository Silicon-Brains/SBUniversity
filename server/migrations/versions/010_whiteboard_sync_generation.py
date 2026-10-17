"""Add board generation for incremental whiteboard synchronization.

Revision ID: 010_whiteboard_sync_generation
Revises: 009_whiteboard_creator
Create Date: 2026-10-17
"""
from alembic import op
import sqlalchemy as sa

revision = "010_whiteboard_sync_generation"
down_revision = "009_whiteboard_creator"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "whiteboard_sessions",
        sa.Column(
            "board_generation",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )


def downgrade() -> None:
    op.drop_column("whiteboard_sessions", "board_generation")
