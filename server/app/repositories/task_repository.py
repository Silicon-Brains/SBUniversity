import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models.course import Course
from app.db.models.task import CompletionStatus, Task, TaskCompletion, TaskStatus, TaskType
from app.db.models.user import User


class TaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, task_id: uuid.UUID) -> Optional[Task]:
        stmt = select(Task).options(selectinload(Task.course), selectinload(Task.creator)).where(Task.id == task_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_exam_id(self, exam_id: uuid.UUID) -> Optional[Task]:
        stmt = select(Task).where(Task.exam_id == exam_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_tasks(
        self,
        course_id: Optional[uuid.UUID] = None,
        status: Optional[TaskStatus] = None,
        task_type: Optional[TaskType] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[Task], int]:
        stmt = select(Task).options(selectinload(Task.course))
        count_stmt = select(func.count(Task.id))

        if course_id:
            stmt = stmt.where(Task.course_id == course_id)
            count_stmt = count_stmt.where(Task.course_id == course_id)
        if status:
            stmt = stmt.where(Task.status == status)
            count_stmt = count_stmt.where(Task.status == status)
        if task_type:
            stmt = stmt.where(Task.type == task_type)
            count_stmt = count_stmt.where(Task.type == task_type)

        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()

        stmt = stmt.order_by(Task.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        res = await self.db.execute(stmt)
        return list(res.scalars().all()), total

    async def create(self, task: Task) -> Task:
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def update(self, task: Task) -> Task:
        await self.db.commit()
        await self.db.refresh(task)
        return task

    # Task completions
    async def get_completion(self, task_id: uuid.UUID, student_id: uuid.UUID) -> Optional[TaskCompletion]:
        stmt = select(TaskCompletion).options(selectinload(TaskCompletion.task)).where(
            TaskCompletion.task_id == task_id,
            TaskCompletion.student_id == student_id,
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_completion_by_id(self, completion_id: uuid.UUID) -> Optional[TaskCompletion]:
        stmt = (
            select(TaskCompletion)
            .options(
                selectinload(TaskCompletion.task).selectinload(Task.course),
                selectinload(TaskCompletion.student),
                selectinload(TaskCompletion.reviewer),
            )
            .where(TaskCompletion.id == completion_id)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def count_task_completions(self, task_id: uuid.UUID) -> int:
        stmt = select(func.count(TaskCompletion.id)).where(TaskCompletion.task_id == task_id)
        res = await self.db.execute(stmt)
        return res.scalar_one()

    async def create_or_ignore_exam_completion(self, task: Task, student_id: uuid.UUID) -> Optional[TaskCompletion]:
        """
        Idempotent completion for exam tasks.
        If completion already exists, does nothing and returns existing or None.
        """
        existing = await self.get_completion(task.id, student_id)
        if existing:
            return existing

        now = datetime.now(timezone.utc)
        completion = TaskCompletion(
            task_id=task.id,
            student_id=student_id,
            status=CompletionStatus.COMPLETED,
            points_awarded=task.points,
            submitted_at=now,
            completed_at=now,
        )
        self.db.add(completion)
        # We don't commit here so the caller can include it in the grading transaction
        await self.db.flush()
        return completion

    async def list_pending_reviews(self, course_ids: Optional[List[uuid.UUID]] = None) -> List[TaskCompletion]:
        stmt = (
            select(TaskCompletion)
            .join(Task, Task.id == TaskCompletion.task_id)
            .options(
                selectinload(TaskCompletion.task).selectinload(Task.course),
                selectinload(TaskCompletion.student),
            )
            .where(TaskCompletion.status == CompletionStatus.PENDING_REVIEW)
        )
        if course_ids:
            stmt = stmt.where(Task.course_id.in_(course_ids))

        stmt = stmt.order_by(TaskCompletion.submitted_at.asc())
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def list_student_completions(self, student_id: uuid.UUID) -> List[TaskCompletion]:
        stmt = (
            select(TaskCompletion)
            .options(selectinload(TaskCompletion.task).selectinload(Task.course))
            .where(TaskCompletion.student_id == student_id)
            .order_by(TaskCompletion.submitted_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def get_student_points_summary(self, student_id: uuid.UUID) -> Tuple[int, int, Optional[datetime]]:
        """
        Returns (total_points, tasks_completed, last_completed_at)
        Only considers status = 'completed'.
        """
        stmt = select(
            func.coalesce(func.sum(TaskCompletion.points_awarded), 0),
            func.count(TaskCompletion.id),
            func.max(TaskCompletion.completed_at),
        ).where(
            TaskCompletion.student_id == student_id,
            TaskCompletion.status == CompletionStatus.COMPLETED,
        )
        res = await self.db.execute(stmt)
        row = res.one()
        return int(row[0]), int(row[1]), row[2]

    async def get_top_students_sql(self, course_id: Optional[uuid.UUID] = None, limit: int = 4) -> List[Tuple[uuid.UUID, str, Optional[str], int, int, datetime]]:
        """
        Database fallback for leaderboard:
        Returns list of (student_id, name, avatar_url, points, tasks_completed, last_completed_at)
        """
        stmt = (
            select(
                TaskCompletion.student_id,
                User.full_name,
                User.avatar_url,
                func.sum(TaskCompletion.points_awarded).label("points"),
                func.count(TaskCompletion.id).label("tasks_completed"),
                func.max(TaskCompletion.completed_at).label("last_completed_at"),
            )
            .join(User, User.id == TaskCompletion.student_id)
            .join(Task, Task.id == TaskCompletion.task_id)
            .where(
                TaskCompletion.status == CompletionStatus.COMPLETED,
                User.status == "active",
            )
        )
        if course_id:
            stmt = stmt.where(Task.course_id == course_id)

        stmt = (
            stmt.group_by(TaskCompletion.student_id, User.full_name, User.avatar_url)
            .having(func.sum(TaskCompletion.points_awarded) > 0)
            .order_by(
                func.sum(TaskCompletion.points_awarded).desc(),
                func.max(TaskCompletion.completed_at).asc(),
            )
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        return list(res.all())
