import uuid
from typing import List, Optional
from pydantic import BaseModel


class OverviewAnalyticsResponse(BaseModel):
    total_students: int
    active_students_now: int
    total_teachers: int
    total_courses: int
    total_exams: int
    total_submissions: int
    overall_average_score: float
    overall_pass_rate: float
    total_tasks: int
    total_task_completions: int
    total_task_points_awarded: int


class TeacherAnalyticsItem(BaseModel):
    teacher_id: uuid.UUID
    teacher_name: str
    department_name: Optional[str] = None
    courses_count: int
    exams_created: int
    total_submissions: int
    average_score: float
    pass_rate: float


class StudentAnalyticsItem(BaseModel):
    student_id: uuid.UUID
    student_name: str
    student_code: str
    department_name: Optional[str] = None
    courses_enrolled: int
    exams_taken: int
    average_score: float
    tasks_completed: int
    total_points: int


class PublicStatsResponse(BaseModel):
    total_students: int
    total_courses: int
    total_exams: int
    total_certificates_issued: int
