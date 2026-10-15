import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user, require_role
from app.db.models.course import Course, Enrollment, EnrollmentStatus
from app.db.models.task import CompletionStatus, Task, TaskCompletion, TaskStatus
from app.db.models.user import User, UserRole
from app.db.session import get_db
from app.repositories.course_repository import CourseRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.task import (
    TaskCompleteRequest,
    TaskCompletionResponse,
    TaskCreate,
    TaskResponse,
    TaskReviewRequest,
    TaskUpdate,
)
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    course_id: Optional[uuid.UUID] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = TaskRepository(db)
    course_repo = CourseRepository(db)

    if current_user.role == UserRole.STUDENT:
        enrollments = await course_repo.list_student_enrollments(current_user.id)
        enrolled_ids = [e.course_id for e in enrollments if e.status == EnrollmentStatus.ACTIVE]
        if not enrolled_ids:
            return []

        tasks, _ = await repo.list_tasks(status=TaskStatus.ACTIVE)
        filtered_tasks = [t for t in tasks if t.course_id in enrolled_ids and (not course_id or t.course_id == course_id)]

        # Attach student's completion status
        completions = await repo.list_student_completions(current_user.id)
        comp_map = {c.task_id: c for c in completions}

        result = []
        for t in filtered_tasks:
            t_resp = TaskResponse.model_validate(t)
            t_resp.course_title = t.course.title if t.course else "Course"
            comp = comp_map.get(t.id)
            if comp:
                t_resp.my_completion_id = comp.id
                t_resp.my_status = comp.status
                t_resp.points_earned = comp.points_awarded if comp.status == CompletionStatus.COMPLETED else 0
            else:
                t_resp.my_status = None
                t_resp.points_earned = 0
            result.append(t_resp)
        return result

    elif current_user.role == UserRole.TEACHER:
        # Teacher's own courses
        courses_stmt = select(Course.id).where(Course.teacher_id == current_user.id)
        teacher_c_ids = (await db.execute(courses_stmt)).scalars().all()
        tasks, _ = await repo.list_tasks(course_id=course_id)
        filtered_tasks = [t for t in tasks if t.course_id in teacher_c_ids]
        res = []
        for t in filtered_tasks:
            t_resp = TaskResponse.model_validate(t)
            t_resp.course_title = t.course.title if t.course else "Course"
            res.append(t_resp)
        return res

    else:
        # Admin
        tasks, _ = await repo.list_tasks(course_id=course_id)
        res = []
        for t in tasks:
            t_resp = TaskResponse.model_validate(t)
            t_resp.course_title = t.course.title if t.course else "Course"
            res.append(t_resp)
        return res


@router.get("/reviews", response_model=List[TaskCompletionResponse])
async def list_pending_reviews(
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    repo = TaskRepository(db)
    course_ids = None
    if current_user.role == UserRole.TEACHER:
        courses_stmt = select(Course.id).where(Course.teacher_id == current_user.id)
        course_ids = list((await db.execute(courses_stmt)).scalars().all())

    completions = await repo.list_pending_reviews(course_ids=course_ids)
    res = []
    for c in completions:
        cr = TaskCompletionResponse.model_validate(c)
        cr.student_name = c.student.full_name if c.student else "Student"
        cr.task_title = c.task.title if c.task else "Task"
        cr.course_title = c.task.course.title if c.task and c.task.course else "Course"
        cr.course_id = c.task.course_id if c.task else None
        res.append(cr)
    return res


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_detail(
    task_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = TaskRepository(db)
    task = await repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    t_resp = TaskResponse.model_validate(task)
    t_resp.course_title = task.course.title if task.course else "Course"

    if current_user.role == UserRole.STUDENT:
        comp = await repo.get_completion(task.id, current_user.id)
        if comp:
            t_resp.my_completion_id = comp.id
            t_resp.my_status = comp.status
            t_resp.points_earned = comp.points_awarded if comp.status == CompletionStatus.COMPLETED else 0

    return t_resp


@router.post("", response_model=TaskResponse)
async def create_assignment_task(
    data: TaskCreate,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    service = TaskService(db)
    task = await service.create_assignment_task(data, current_user)
    t_resp = TaskResponse.model_validate(task)
    t_resp.course_title = task.course.title if task.course else "Course"
    return t_resp


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: uuid.UUID,
    data: TaskUpdate,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    service = TaskService(db)
    task = await service.update_task(task_id, data, current_user)
    t_resp = TaskResponse.model_validate(task)
    t_resp.course_title = task.course.title if task.course else "Course"
    return t_resp


@router.post("/{task_id}/archive", response_model=TaskResponse)
async def archive_task(
    task_id: uuid.UUID,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    service = TaskService(db)
    task = await service.archive_task(task_id, current_user)
    t_resp = TaskResponse.model_validate(task)
    t_resp.course_title = task.course.title if task.course else "Course"
    return t_resp


@router.post("/{task_id}/complete")
async def submit_assignment_task(
    task_id: uuid.UUID,
    body: TaskCompleteRequest,
    current_user: User = Depends(require_role(UserRole.STUDENT)),
    db: AsyncSession = Depends(get_db),
):
    service = TaskService(db)
    completion = await service.submit_assignment(task_id, current_user.id, body.note, body.url)
    return {
        "completion_id": str(completion.id),
        "status": completion.status.value,
        "submitted_at": completion.submitted_at.isoformat(),
    }


@router.post("/completions/{completion_id}/approve")
async def approve_task_completion(
    completion_id: uuid.UUID,
    body: TaskReviewRequest,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    service = TaskService(db)
    comp = await service.approve_assignment(completion_id, current_user, body.review_note)
    return {
        "status": comp.status.value,
        "points_awarded": comp.points_awarded,
        "completed_at": comp.completed_at.isoformat() if comp.completed_at else None,
    }


@router.post("/completions/{completion_id}/reject")
async def reject_task_completion(
    completion_id: uuid.UUID,
    body: TaskReviewRequest,
    current_user: User = Depends(require_role([UserRole.TEACHER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db),
):
    service = TaskService(db)
    comp = await service.reject_assignment(completion_id, current_user, body.review_note)
    return {
        "status": comp.status.value,
        "points_awarded": 0,
    }
