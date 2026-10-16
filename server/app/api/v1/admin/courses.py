from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user, require_role
from app.core.logging import logger
from app.db.models.course import Course
from app.db.models.user import User
from app.db.models.user import UserRole
from app.db.session import get_db
from app.schemas.course import AdminCourseCreate, AdminCourseResponse
from app.services.course_service import CourseService

router = APIRouter(
    prefix="/courses",
    tags=["Admin Courses"],
    dependencies=[Depends(require_role(UserRole.ADMIN))],
)


@router.get("", response_model=List[AdminCourseResponse])
async def list_admin_courses(db: AsyncSession = Depends(get_db)):
    courses = await CourseService(db).list_admin_courses()
    return [
        AdminCourseResponse.model_validate(course).model_copy(
            update={"enrolled_students": enrolled_count}
        )
        for course, enrolled_count in courses
    ]


@router.post("", response_model=AdminCourseResponse, status_code=status.HTTP_201_CREATED)
async def create_admin_course(
    data: AdminCourseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        course, enrolled_count = await CourseService(db).create_admin_course(
            data, current_user
        )
    except IntegrityError as exc:
        logger.warning("Admin course creation failed due to database constraint: %s", exc.orig)
        existing_course = await db.scalar(
            select(Course.id).where(Course.code == data.code.strip().upper())
        )
        if existing_course:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A course with this code already exists.",
            ) from exc
        raise

    response = AdminCourseResponse.model_validate(course)
    response.enrolled_students = enrolled_count
    return response
