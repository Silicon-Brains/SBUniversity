"""Fix legacy task check constraint name for auto-awarded assignments.

Revision ID: 004_fix_task_type_check_constraint
Revises: 003_auto_award_assignment_points
Create Date: 2026-10-16
"""
from alembic import op

revision = "004_fix_task_type_check_constraint"
down_revision = "003_auto_award_assignment_points"
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
    op.drop_constraint("ck_task_type_verification", "tasks", type_="check")
    op.create_check_constraint(
        "ck_task_type_exam",
        "tasks",
        "(type = 'exam' AND exam_id IS NOT NULL AND verification = 'auto') OR "
        "(type = 'assignment' AND exam_id IS NULL AND verification = 'teacher_approval')",
    )
