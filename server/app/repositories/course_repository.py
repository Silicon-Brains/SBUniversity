import uuid
from typing import List, Optional, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models.course import Course, CourseTeacher, Enrollment, EnrollmentStatus


class CourseRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, course_id: uuid.UUID) -> Optional[Course]:
        stmt = (
            select(Course)
            .options(
                selectinload(Course.department),
                selectinload(Course.teacher),
                selectinload(Course.teacher_assignments),
                selectinload(Course.enrollments),
            )
            .where(Course.id == course_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_code(self, code: str) -> Optional[Course]:
        stmt = select(Course).where(Course.code == code)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_courses(
        self,
        teacher_id: Optional[uuid.UUID] = None,
        is_published: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Course], int]:
        stmt = select(Course).options(selectinload(Course.department), selectinload(Course.teacher))
        count_stmt = select(func.count(Course.id))

        if teacher_id:
            teacher_filter = or_(
                Course.teacher_id == teacher_id,
                Course.teacher_assignments.any(CourseTeacher.teacher_id == teacher_id),
            )
            stmt = stmt.where(teacher_filter)
            count_stmt = count_stmt.where(teacher_filter)
        if is_published is not None:
            stmt = stmt.where(Course.is_published == is_published)
            count_stmt = count_stmt.where(Course.is_published == is_published)

        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()

        stmt = stmt.order_by(Course.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        res = await self.db.execute(stmt)
        return list(res.scalars().all()), total

    async def is_teacher_assigned(
        self, course_id: uuid.UUID, teacher_id: uuid.UUID
    ) -> bool:
        result = await self.db.scalar(
            select(Course.id).where(
                Course.id == course_id,
                or_(
                    Course.teacher_id == teacher_id,
                    Course.teacher_assignments.any(
                        CourseTeacher.teacher_id == teacher_id
                    ),
                ),
            )
        )
        return result is not None

    async def create(self, course: Course) -> Course:
        self.db.add(course)
        await self.db.commit()
        await self.db.refresh(course)
        return course

    async def update(self, course: Course) -> Course:
        await self.db.commit()
        return (await self.get_by_id(course.id)) or course

    # Enrollments
    async def get_enrollment(self, student_id: uuid.UUID, course_id: uuid.UUID) -> Optional[Enrollment]:
        stmt = select(Enrollment).options(selectinload(Enrollment.course)).where(
            Enrollment.student_id == student_id,
            Enrollment.course_id == course_id,
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_student_enrollments(self, student_id: uuid.UUID) -> List[Enrollment]:
        stmt = (
            select(Enrollment)
            .options(selectinload(Enrollment.course))
            .where(Enrollment.student_id == student_id)
            .order_by(Enrollment.enrolled_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create_enrollment(self, enrollment: Enrollment) -> Enrollment:
        self.db.add(enrollment)
        await self.db.commit()
        await self.db.refresh(enrollment)
        return enrollment

    async def update_enrollment(self, enrollment: Enrollment) -> Enrollment:
        await self.db.commit()
        await self.db.refresh(enrollment)
        return enrollment
