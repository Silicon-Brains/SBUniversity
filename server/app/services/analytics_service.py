import json
import uuid
from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.redis import get_redis_client
from app.db.models.course import Course, Enrollment
from app.db.models.exam import Exam
from app.db.models.result import Result
from app.db.models.task import CompletionStatus, Task, TaskCompletion
from app.db.models.user import Department, StudentProfile, TeacherProfile, User, UserRole, UserStatus
from app.schemas.analytics import OverviewAnalyticsResponse, PublicStatsResponse, StudentAnalyticsItem, TeacherAnalyticsItem


class AnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_overview_analytics(self) -> OverviewAnalyticsResponse:
        redis = await get_redis_client()
        cached = await redis.get("cache:admin:analytics:overview")
        if cached:
            try:
                return OverviewAnalyticsResponse(**json.loads(cached))
            except Exception:
                pass

        # Counts
        total_students_res = await self.db.execute(select(func.count(User.id)).where(User.role == UserRole.STUDENT, User.status != UserStatus.DELETED))
        total_students = total_students_res.scalar() or 0

        active_students_res = await self.db.execute(select(func.count(User.id)).where(User.role == UserRole.STUDENT, User.status == UserStatus.ACTIVE))
        active_students = active_students_res.scalar() or 0

        total_teachers_res = await self.db.execute(select(func.count(User.id)).where(User.role == UserRole.TEACHER, User.status == UserStatus.ACTIVE))
        total_teachers = total_teachers_res.scalar() or 0

        total_courses_res = await self.db.execute(select(func.count(Course.id)))
        total_courses = total_courses_res.scalar() or 0

        total_exams_res = await self.db.execute(select(func.count(Exam.id)))
        total_exams = total_exams_res.scalar() or 0

        # Submissions & scores
        total_sub_res = await self.db.execute(select(func.count(Result.id)))
        total_submissions = total_sub_res.scalar() or 0

        avg_score_res = await self.db.execute(select(func.avg(Result.percentage)))
        overall_avg_score = round(float(avg_score_res.scalar() or 0.0), 2)

        pass_cnt_res = await self.db.execute(select(func.count(Result.id)).where(Result.passed == True))
        pass_count = pass_cnt_res.scalar() or 0
        pass_rate = round((pass_count / total_submissions * 100.0) if total_submissions > 0 else 0.0, 2)

        # Tasks
        total_tasks_res = await self.db.execute(select(func.count(Task.id)))
        total_tasks = total_tasks_res.scalar() or 0

        total_comps_res = await self.db.execute(select(func.count(TaskCompletion.id)).where(TaskCompletion.status == CompletionStatus.COMPLETED))
        total_task_comps = total_comps_res.scalar() or 0

        total_points_res = await self.db.execute(select(func.sum(TaskCompletion.points_awarded)).where(TaskCompletion.status == CompletionStatus.COMPLETED))
        total_points_awarded = int(total_points_res.scalar() or 0)

        response = OverviewAnalyticsResponse(
            total_students=total_students,
            active_students_now=active_students,
            total_teachers=total_teachers,
            total_courses=total_courses,
            total_exams=total_exams,
            total_submissions=total_submissions,
            overall_average_score=overall_avg_score,
            overall_pass_rate=pass_rate,
            total_tasks=total_tasks,
            total_task_completions=total_task_comps,
            total_task_points_awarded=total_points_awarded,
        )

        await redis.set("cache:admin:analytics:overview", json.dumps(response.model_dump()), ex=45)
        return response

    async def get_teacher_analytics(self) -> List[TeacherAnalyticsItem]:
        stmt = (
            select(User)
            .options(
                selectinload(User.teacher_profile).selectinload(TeacherProfile.department),
                selectinload(User.courses_taught),
            )
            .where(User.role == UserRole.TEACHER, User.status == UserStatus.ACTIVE)
        )
        res = await self.db.execute(stmt)
        teachers = list(res.scalars().all())

        items: List[TeacherAnalyticsItem] = []
        for t in teachers:
            c_ids = [c.id for c in t.courses_taught]
            courses_count = len(c_ids)

            exams_cnt = 0
            sub_cnt = 0
            avg_score = 0.0
            pass_rate = 0.0

            if c_ids:
                stmt_exams = select(func.count(Exam.id)).where(Exam.course_id.in_(c_ids))
                ex_res = await self.db.execute(stmt_exams)
                exams_cnt = ex_res.scalar() or 0

                stmt_res = (
                    select(
                        func.count(Result.id),
                        func.avg(Result.percentage),
                        func.count(Result.id).filter(Result.passed == True),
                    )
                    .join(Exam, Exam.id == Result.exam_id)
                    .where(Exam.course_id.in_(c_ids))
                )
                r_stats = (await self.db.execute(stmt_res)).one()
                sub_cnt = r_stats[0] or 0
                avg_score = round(float(r_stats[1] or 0.0), 2)
                passed_cnt = r_stats[2] or 0
                pass_rate = round((passed_cnt / sub_cnt * 100.0) if sub_cnt > 0 else 0.0, 2)

            dept_name = t.teacher_profile.department.name if t.teacher_profile and t.teacher_profile.department else None

            items.append(
                TeacherAnalyticsItem(
                    teacher_id=t.id,
                    teacher_name=t.full_name,
                    department_name=dept_name,
                    courses_count=courses_count,
                    exams_created=exams_cnt,
                    total_submissions=sub_cnt,
                    average_score=avg_score,
                    pass_rate=pass_rate,
                )
            )
        return items

    async def get_student_analytics(self, limit: int = 50) -> List[StudentAnalyticsItem]:
        stmt = (
            select(User)
            .options(
                selectinload(User.student_profile).selectinload(StudentProfile.department),
                selectinload(User.enrollments),
            )
            .where(User.role == UserRole.STUDENT, User.status == UserStatus.ACTIVE)
            .limit(limit)
        )
        res = await self.db.execute(stmt)
        students = list(res.scalars().all())

        items: List[StudentAnalyticsItem] = []
        for s in students:
            enrolled_cnt = len(s.enrollments)

            # Exam stats
            stmt_r = select(
                func.count(Result.id),
                func.avg(Result.percentage),
            ).where(Result.student_id == s.id)
            r_stats = (await self.db.execute(stmt_r)).one()
            exams_taken = r_stats[0] or 0
            avg_score = round(float(r_stats[1] or 0.0), 2)

            # Task points
            stmt_t = select(
                func.count(TaskCompletion.id),
                func.sum(TaskCompletion.points_awarded),
            ).where(
                TaskCompletion.student_id == s.id,
                TaskCompletion.status == CompletionStatus.COMPLETED,
            )
            t_stats = (await self.db.execute(stmt_t)).one()
            tasks_comp = t_stats[0] or 0
            total_pts = int(t_stats[1] or 0)

            dept_name = s.student_profile.department.name if s.student_profile and s.student_profile.department else None
            student_code = s.student_profile.student_code if s.student_profile else "SBU-0000"

            items.append(
                StudentAnalyticsItem(
                    student_id=s.id,
                    student_name=s.full_name,
                    student_code=student_code,
                    department_name=dept_name,
                    courses_enrolled=enrolled_cnt,
                    exams_taken=exams_taken,
                    average_score=avg_score,
                    tasks_completed=tasks_comp,
                    total_points=total_pts,
                )
            )
        return items

    async def get_public_stats(self) -> PublicStatsResponse:
        redis = await get_redis_client()
        cached = await redis.get("cache:public:stats")
        if cached:
            try:
                return PublicStatsResponse(**json.loads(cached))
            except Exception:
                pass

        total_st = (await self.db.execute(select(func.count(User.id)).where(User.role == UserRole.STUDENT))).scalar() or 0
        total_co = (await self.db.execute(select(func.count(Course.id)).where(Course.is_published == True))).scalar() or 0
        total_ex = (await self.db.execute(select(func.count(Exam.id)).where(Exam.status == "published"))).scalar() or 0
        total_ce = (await self.db.execute(select(func.count(Result.id)).where(Result.passed == True))).scalar() or 0

        res = PublicStatsResponse(
            total_students=total_st,
            total_courses=total_co,
            total_exams=total_ex,
            total_certificates_issued=total_ce,
        )
        await redis.set("cache:public:stats", json.dumps(res.model_dump()), ex=300)
        return res
