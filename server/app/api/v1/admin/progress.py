import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.deps import get_current_user, require_role
from app.db.models.course import Course, Enrollment
from app.db.models.exam import Exam
from app.db.models.task import CompletionStatus, TaskCompletion
from app.db.models.user import StudentProfile, User, UserRole
from app.db.session import get_db
from app.schemas.certificate import CertificateResponse, RevokeCertificateRequest
from app.services.certificate_service import CertificateService
from app.services.task_service import TaskService

router = APIRouter(prefix="/progress", tags=["Admin Progress"], dependencies=[Depends(require_role(UserRole.ADMIN))])


@router.get("/students")
async def get_students_progress(
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(User)
        .options(
            selectinload(User.student_profile),
            selectinload(User.enrollments).selectinload(Enrollment.course),
        )
        .where(User.role == UserRole.STUDENT)
    )
    if search:
        term = f"%{search.lower()}%"
        stmt = stmt.where(func.lower(User.full_name).like(term) | func.lower(User.email).like(term))

    count_stmt = select(func.count(User.id)).where(User.role == UserRole.STUDENT)
    if search:
        count_stmt = count_stmt.where(func.lower(User.full_name).like(term) | func.lower(User.email).like(term))

    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    res = await db.execute(stmt)
    students = list(res.scalars().all())

    items = []
    task_service = TaskService(db)
    for s in students:
        pts = await task_service.get_student_points(s.id)
        courses_data = [
            {
                "course_id": str(e.course_id),
                "course_title": e.course.title if e.course else "Course",
                "progress_percent": float(e.progress_percent),
                "status": e.status.value,
            }
            for e in s.enrollments
        ]
        items.append({
            "student_id": str(s.id),
            "name": s.full_name,
            "email": s.email,
            "student_code": s.student_profile.student_code if s.student_profile else "SBU-0000",
            "total_points": pts.total_points,
            "tasks_completed": pts.tasks_completed,
            "rank": pts.rank,
            "courses": courses_data,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/tasks/completions/{completion_id}/revoke")
async def revoke_student_task_completion(
    completion_id: uuid.UUID,
    reason: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = TaskService(db)
    comp = await service.revoke_completion(completion_id, current_user, reason)
    return {
        "completion_id": str(comp.id),
        "status": comp.status.value,
        "points_awarded": comp.points_awarded,
    }


@router.post("/certificates/{certificate_id}/revoke", response_model=CertificateResponse)
async def revoke_student_certificate(
    certificate_id: uuid.UUID,
    body: RevokeCertificateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CertificateService(db)
    cert = await service.revoke_certificate(certificate_id, current_user, body.reason)
    return cert
