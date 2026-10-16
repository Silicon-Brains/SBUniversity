"""Add student community and staff support chat.

Revision ID: 006_community_chat
Revises: 005_task_video_progress
Create Date: 2026-10-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "006_community_chat"
down_revision = "005_task_video_progress"
branch_labels = None
depends_on = None

conversation_kind = postgresql.ENUM(
    "student_room",
    "peer_direct",
    "admin_support",
    "teacher_support",
    name="community_conversation_kind",
    create_type=False,
)


def upgrade() -> None:
    conversation_kind.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "community_conversations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "kind",
            conversation_kind,
            nullable=False,
        ),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("room_key", sa.String(length=64), nullable=True),
        sa.Column(
            "peer_one_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "peer_two_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column(
            "requester_student_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.UniqueConstraint("room_key", name="uq_community_conversation_room_key"),
        sa.UniqueConstraint(
            "peer_one_id",
            "peer_two_id",
            name="uq_community_conversation_peer_pair",
        ),
        sa.UniqueConstraint(
            "requester_student_id",
            "kind",
            name="uq_community_conversation_student_support_kind",
        ),
        sa.CheckConstraint(
            "(kind = 'student_room' AND room_key IS NOT NULL "
            "AND peer_one_id IS NULL AND peer_two_id IS NULL "
            "AND requester_student_id IS NULL) OR "
            "(kind = 'peer_direct' AND room_key IS NULL "
            "AND peer_one_id IS NOT NULL AND peer_two_id IS NOT NULL "
            "AND peer_one_id < peer_two_id AND requester_student_id IS NULL) OR "
            "(kind IN ('admin_support', 'teacher_support') "
            "AND room_key IS NULL AND peer_one_id IS NULL AND peer_two_id IS NULL "
            "AND requester_student_id IS NOT NULL)",
            name="ck_community_conversation_target",
        ),
    )
    op.create_index(
        "ix_community_conversations_kind",
        "community_conversations",
        ["kind"],
    )
    op.create_index(
        "ix_community_conversations_expires_at",
        "community_conversations",
        ["expires_at"],
    )
    op.create_index(
        "ix_community_conversations_requester_student_id",
        "community_conversations",
        ["requester_student_id"],
    )
    op.create_table(
        "community_messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("community_conversations.id", ondelete="CASCADE"),
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
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "length(content) > 0 AND length(content) <= 4000",
            name="ck_community_message_content_length",
        ),
    )
    op.create_index(
        "ix_community_messages_conversation_id",
        "community_messages",
        ["conversation_id"],
    )
    op.create_index(
        "ix_community_messages_sender_id",
        "community_messages",
        ["sender_id"],
    )
    op.create_index(
        "ix_community_messages_created_at",
        "community_messages",
        ["created_at"],
    )
    op.create_index(
        "ix_community_messages_conversation_created",
        "community_messages",
        ["conversation_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_community_messages_conversation_created",
        table_name="community_messages",
    )
    op.drop_index("ix_community_messages_created_at", table_name="community_messages")
    op.drop_index("ix_community_messages_sender_id", table_name="community_messages")
    op.drop_index(
        "ix_community_messages_conversation_id",
        table_name="community_messages",
    )
    op.drop_table("community_messages")
    op.drop_index(
        "ix_community_conversations_requester_student_id",
        table_name="community_conversations",
    )
    op.drop_index(
        "ix_community_conversations_expires_at",
        table_name="community_conversations",
    )
    op.drop_index(
        "ix_community_conversations_kind",
        table_name="community_conversations",
    )
    op.drop_table("community_conversations")
    conversation_kind.drop(op.get_bind(), checkfirst=True)
