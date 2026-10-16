"""Allow resource assignments to award points on completion.

Revision ID: 003_auto_award_assignment_points
Revises: 002_task_resources_recipients
Create Date: 2026-10-16
"""
from alembic import op

revision = "003_auto_award_assignment_points"
down_revision = "002_task_resources_recipients"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE tasks "
        "DROP CONSTRAINT IF EXISTS ck_task_type_exam, "
        "DROP CONSTRAINT IF EXISTS ck_task_type_verification"
    )
    op.create_check_constraint(
        "ck_task_type_verification",
        "tasks",
        "(type = 'exam' AND exam_id IS NOT NULL AND verification = 'auto') OR "
        "(type = 'assignment' AND exam_id IS NULL AND "
        "verification IN ('auto', 'teacher_approval'))",
    )


def downgrade() -> None:
    op.execute(
        "UPDATE tasks SET verification = 'teacher_approval' "
        "WHERE type = 'assignment' AND verification = 'auto'"
    )
    op.execute(
        "ALTER TABLE tasks "
        "DROP CONSTRAINT IF EXISTS ck_task_type_exam, "
        "DROP CONSTRAINT IF EXISTS ck_task_type_verification"
    )
    op.create_check_constraint(
        "ck_task_type_verification",
        "tasks",
        "(type = 'exam' AND exam_id IS NOT NULL AND verification = 'auto') OR "
        "(type = 'assignment' AND exam_id IS NULL AND verification = 'teacher_approval')",
    )
