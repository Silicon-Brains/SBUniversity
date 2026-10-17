"""Add personal Learn Planner entries and voice notes.

Revision ID: 007_learn_planner
Revises: 006_community_chat
Create Date: 2026-10-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "007_learn_planner"
down_revision = "006_community_chat"
branch_labels = None
depends_on = None

entry_kind = postgresql.ENUM(
    "learning_plan",
    "note",
    "sticky_note",
    "event",
    "voice_note",
    name="planner_entry_kind",
    create_type=False,
)
note_shape = postgresql.ENUM(
    "rectangle",
    "rounded",
    "circle",
    "cloud",
    "star",
    name="planner_note_shape",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    entry_kind.create(bind, checkfirst=True)
    note_shape.create(bind, checkfirst=True)

    op.create_table(
        "planner_entries",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", entry_kind, nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("color", sa.String(length=7), nullable=False, server_default="#fef3c7"),
        sa.Column("shape", note_shape, nullable=False, server_default=sa.text("'rounded'")),
        sa.Column("emoji", sa.String(length=16), nullable=True),
        sa.Column("audio_path", sa.String(length=512), nullable=True),
        sa.Column("audio_mime_type", sa.String(length=100), nullable=True),
        sa.Column("audio_size_bytes", sa.Integer(), nullable=True),
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
        sa.CheckConstraint(
            "audio_size_bytes IS NULL OR "
            "(audio_size_bytes > 0 AND audio_size_bytes <= 26214400)",
            name="ck_planner_entry_audio_size",
        ),
        sa.CheckConstraint(
            "(kind = 'voice_note' AND audio_path IS NOT NULL "
            "AND audio_mime_type IS NOT NULL AND audio_size_bytes IS NOT NULL) OR "
            "(kind != 'voice_note' AND audio_path IS NULL "
            "AND audio_mime_type IS NULL AND audio_size_bytes IS NULL)",
            name="ck_planner_entry_audio_fields",
        ),
        sa.CheckConstraint(
            "length(color) = 7 AND substr(color, 1, 1) = '#'",
            name="ck_planner_entry_color",
        ),
    )
    op.create_index("ix_planner_entries_owner_id", "planner_entries", ["owner_id"])
    op.create_index("ix_planner_entries_kind", "planner_entries", ["kind"])
    op.create_index(
        "ix_planner_entries_owner_kind_due",
        "planner_entries",
        ["owner_id", "kind", "due_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_planner_entries_owner_kind_due", table_name="planner_entries")
    op.drop_index("ix_planner_entries_kind", table_name="planner_entries")
    op.drop_index("ix_planner_entries_owner_id", table_name="planner_entries")
    op.drop_table("planner_entries")
    note_shape.drop(op.get_bind(), checkfirst=True)
    entry_kind.drop(op.get_bind(), checkfirst=True)
