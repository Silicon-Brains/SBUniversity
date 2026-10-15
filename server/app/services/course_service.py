import uuid
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.course import Course, Enrollment, EnrollmentStatus
from app.db.models.user import User, UserRole
from app.repositories.course_repository import CourseRepository
from app.repositories.user_repository import UserRepository
from app.schemas.course import CourseCreate, CourseUpdate


class CourseService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.course_repo = CourseRepository(db)
        self.user_repo = UserRepository(db)

    async def create_course(self, data: CourseCreate, creator: User) -> Course:
        teacher_id = data.teacher_id or creator.id
        if creator.role == UserRole.TEACHER:
            teacher_id = creator.id

        course = Course(
            code=data.code,
            title=data.title,
            description=data.description,
            department_id=data.department_id,
            teacher_id=teacher_id,
            is_published=data.is_published,
        )
        return await self.course_repo.create(course)

    async def update_course(self, course_id: uuid.UUID, data: CourseUpdate, user: User) -> Course:
        course = await self.course_repo.get_by_id(course_id)
        if not course:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

        if user.role == UserRole.TEACHER and course.teacher_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        for field, val in data.model_dump(exclude_unset=True).items():
            setattr(course, field, val)

        return await self.course_repo.update(course)

    async def enroll_student(self, student_id: uuid.UUID, course_id: uuid.UUID) -> Enrollment:
        existing = await self.course_repo.get_enrollment(student_id, course_id)
        if existing:
            return existing

        enrollment = Enrollment(student_id=student_id, course_id=course_id, status=EnrollmentStatus.ACTIVE)
        return await self.course_repo.create_enrollment(enrollment)
