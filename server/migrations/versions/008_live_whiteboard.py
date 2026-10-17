"""Add course live whiteboard sessions, strokes, and expiring class chat.

Revision ID: 008_live_whiteboard
Revises: 007_learn_planner
Create Date: 2026-10-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "008_live_whiteboard"
down_revision = "007_learn_planner"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "whiteboard_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "course_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("courses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "teacher_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index(
        "ix_whiteboard_sessions_course_id",
        "whiteboard_sessions",
        ["course_id"],
    )
    op.create_index(
        "ix_whiteboard_sessions_teacher_id",
        "whiteboard_sessions",
        ["teacher_id"],
    )
    op.create_index(
        "uq_whiteboard_sessions_active_course",
        "whiteboard_sessions",
        ["course_id"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )

    op.create_table(
        "whiteboard_strokes",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("whiteboard_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "author_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tool", sa.String(length=16), nullable=False),
        sa.Column("color", sa.String(length=7), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("points", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "tool IN ('pen', 'eraser', 'line', 'rectangle', 'ellipse')",
            name="ck_whiteboard_stroke_tool",
        ),
        sa.CheckConstraint("width BETWEEN 1 AND 40", name="ck_whiteboard_stroke_width"),
        sa.CheckConstraint(
            "color ~ '^#[0-9a-fA-F]{6}$'",
            name="ck_whiteboard_stroke_color",
        ),
    )
    op.create_index(
        "ix_whiteboard_strokes_session_id",
        "whiteboard_strokes",
        ["session_id"],
    )
    op.create_index(
        "ix_whiteboard_strokes_author_id",
        "whiteboard_strokes",
        ["author_id"],
    )
    op.create_index(
        "ix_whiteboard_strokes_created_at",
        "whiteboard_strokes",
        ["created_at"],
    )
    op.create_index(
        "ix_whiteboard_strokes_session_created",
        "whiteboard_strokes",
        ["session_id", "created_at"],
    )

    op.create_table(
        "whiteboard_messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("whiteboard_sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "sender_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "length(content) > 0 AND length(content) <= 1000",
            name="ck_whiteboard_message_content_length",
        ),
        sa.CheckConstraint(
            "expires_at > created_at",
            name="ck_whiteboard_message_expiry",
        ),
    )
    op.create_index(
        "ix_whiteboard_messages_session_id",
        "whiteboard_messages",
        ["session_id"],
    )
    op.create_index(
        "ix_whiteboard_messages_sender_id",
        "whiteboard_messages",
        ["sender_id"],
    )
    op.create_index(
        "ix_whiteboard_messages_created_at",
        "whiteboard_messages",
        ["created_at"],
    )
    op.create_index(
        "ix_whiteboard_messages_expires_at",
        "whiteboard_messages",
        ["expires_at"],
    )
    op.create_index(
        "ix_whiteboard_messages_session_created",
        "whiteboard_messages",
        ["session_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_whiteboard_messages_session_created",
        table_name="whiteboard_messages",
    )
    op.drop_index(
        "ix_whiteboard_messages_expires_at",
        table_name="whiteboard_messages",
    )
    op.drop_index(
        "ix_whiteboard_messages_created_at",
        table_name="whiteboard_messages",
    )
    op.drop_index(
        "ix_whiteboard_messages_sender_id",
        table_name="whiteboard_messages",
    )
    op.drop_index(
        "ix_whiteboard_messages_session_id",
        table_name="whiteboard_messages",
    )
    op.drop_table("whiteboard_messages")

    op.drop_index(
        "ix_whiteboard_strokes_session_created",
        table_name="whiteboard_strokes",
    )
    op.drop_index(
        "ix_whiteboard_strokes_created_at",
        table_name="whiteboard_strokes",
    )
    op.drop_index(
        "ix_whiteboard_strokes_author_id",
        table_name="whiteboard_strokes",
    )
    op.drop_index(
        "ix_whiteboard_strokes_session_id",
        table_name="whiteboard_strokes",
    )
    op.drop_table("whiteboard_strokes")

    op.drop_index(
        "uq_whiteboard_sessions_active_course",
        table_name="whiteboard_sessions",
    )
    op.drop_index(
        "ix_whiteboard_sessions_teacher_id",
        table_name="whiteboard_sessions",
    )
    op.drop_index(
        "ix_whiteboard_sessions_course_id",
        table_name="whiteboard_sessions",
    )
    op.drop_table("whiteboard_sessions")
