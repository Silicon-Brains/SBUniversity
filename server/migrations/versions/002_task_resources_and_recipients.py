"""Add linked learning resources and student-specific task targeting.

Revision ID: 002_task_resources_recipients
Revises: 001_initial_schema
Create Date: 2026-10-16
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_task_resources_recipients"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


task_resource_type = postgresql.ENUM(
    "video",
    "learning_source",
    name="task_resource_type",
    create_type=False,
)
task_assignment_scope = postgresql.ENUM(
    "all_students",
    "selected_students",
    name="task_assignment_scope",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    task_resource_type.create(bind, checkfirst=True)
    task_assignment_scope.create(bind, checkfirst=True)

    op.add_column(
        "tasks",
        sa.Column("resource_type", task_resource_type, nullable=True),
    )
    op.add_column(
        "tasks",
        sa.Column(
            "resource_url",
            sa.String(),
            nullable=True,
        ),
    )
    op.add_column(
        "tasks",
        sa.Column(
            "assignment_scope",
            task_assignment_scope,
            nullable=False,
            server_default="all_students",
        ),
    )
    op.create_check_constraint(
        "ck_task_resource_type_url",
        "tasks",
        "(resource_type IS NULL AND resource_url IS NULL) OR "
        "(resource_type IS NOT NULL AND resource_url IS NOT NULL)",
    )
    op.create_table(
        "task_recipients",
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
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_task_recipients_student_id",
        "task_recipients",
        ["student_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_task_recipients_student_id", table_name="task_recipients")
    op.drop_table("task_recipients")
    op.drop_constraint("ck_task_resource_type_url", "tasks", type_="check")
    op.drop_column("tasks", "assignment_scope")
    op.drop_column("tasks", "resource_url")
    op.drop_column("tasks", "resource_type")
    task_assignment_scope.drop(op.get_bind(), checkfirst=True)
    task_resource_type.drop(op.get_bind(), checkfirst=True)
