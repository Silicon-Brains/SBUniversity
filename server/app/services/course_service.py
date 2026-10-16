import uuid
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.course import Course, Enrollment, EnrollmentStatus
from app.db.models.user import User, UserRole, UserStatus
from app.repositories.course_repository import CourseRepository
from app.repositories.user_repository import UserRepository
from app.schemas.course import AdminCourseCreate, CourseCreate, CourseUpdate


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

    async def create_admin_course(
        self,
        data: AdminCourseCreate,
        creator: User,
    ) -> tuple[Course, int]:
        course = Course(
            code=data.code.strip().upper(),
            title=data.title.strip(),
            description=data.description,
            department_id=data.department_id,
            teacher_id=creator.id,
            is_published=data.is_published,
        )
        try:
            self.db.add(course)
            await self.db.flush()

            enrolled_students = 0
            if data.enroll_all_active_students:
                active_student_ids = (
                    await self.db.execute(
                        select(User.id).where(
                            User.role == UserRole.STUDENT,
                            User.status == UserStatus.ACTIVE,
                        )
                    )
                ).scalars().all()
                self.db.add_all(
                    Enrollment(
                        student_id=student_id,
                        course_id=course.id,
                        status=EnrollmentStatus.ACTIVE,
                    )
                    for student_id in active_student_ids
                )
                enrolled_students = len(active_student_ids)

            await self.db.commit()
            await self.db.refresh(course)
            return course, enrolled_students
        except Exception:
            await self.db.rollback()
            raise

    async def list_admin_courses(self) -> list[tuple[Course, int]]:
        stmt = (
            select(Course, func.count(Enrollment.id))
            .outerjoin(
                Enrollment,
                (Enrollment.course_id == Course.id)
                & (Enrollment.status == EnrollmentStatus.ACTIVE),
            )
            .group_by(Course.id)
            .order_by(Course.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return [(course, int(count)) for course, count in result.all()]

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
