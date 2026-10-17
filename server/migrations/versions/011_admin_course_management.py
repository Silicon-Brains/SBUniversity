"""Support multiple course teachers and permanent account deletion.

Revision ID: 011_admin_course_management
Revises: 010_whiteboard_sync_generation
Create Date: 2026-10-18
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "011_admin_course_management"
down_revision = "010_whiteboard_sync_generation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "course_teachers",
        sa.Column(
            "course_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("courses.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "teacher_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
    )
    op.create_index(
        "ix_course_teachers_teacher_id",
        "course_teachers",
        ["teacher_id"],
    )
    op.execute(
        """
        INSERT INTO course_teachers (course_id, teacher_id)
        SELECT courses.id, courses.teacher_id
        FROM courses
        JOIN users ON users.id = courses.teacher_id
        WHERE users.role = 'teacher'
        ON CONFLICT (course_id, teacher_id) DO NOTHING
        """
    )

    for table, column, old_constraint in (
        ("exams", "created_by", "exams_created_by_fkey"),
        ("tasks", "created_by", "tasks_created_by_fkey"),
        ("notices", "author_id", "notices_author_id_fkey"),
        (
            "whiteboard_sessions",
            "created_by",
            "whiteboard_sessions_teacher_id_fkey",
        ),
    ):
        op.drop_constraint(old_constraint, table, type_="foreignkey")
        op.alter_column(table, column, existing_type=postgresql.UUID(), nullable=True)
        op.create_foreign_key(
            f"{table}_{column}_fkey",
            table,
            "users",
            [column],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade() -> None:
    for table, column, new_constraint, old_constraint in (
        ("exams", "created_by", "exams_created_by_fkey", "exams_created_by_fkey"),
        ("tasks", "created_by", "tasks_created_by_fkey", "tasks_created_by_fkey"),
        ("notices", "author_id", "notices_author_id_fkey", "notices_author_id_fkey"),
        (
            "whiteboard_sessions",
            "created_by",
            "whiteboard_sessions_created_by_fkey",
            "whiteboard_sessions_teacher_id_fkey",
        ),
    ):
        op.drop_constraint(new_constraint, table, type_="foreignkey")
        op.alter_column(table, column, existing_type=postgresql.UUID(), nullable=False)
        op.create_foreign_key(
            old_constraint,
            table,
            "users",
            [column],
            ["id"],
            ondelete="RESTRICT",
        )

    op.drop_index("ix_course_teachers_teacher_id", table_name="course_teachers")
    op.drop_table("course_teachers")
