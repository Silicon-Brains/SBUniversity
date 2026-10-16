import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Enrollment, EnrollmentStatus, User, UserRole, UserStatus


@pytest.mark.asyncio
async def test_admin_creates_published_course_and_enrolls_all_active_students(
    client: AsyncClient,
    db_session: AsyncSession,
):
    suspended_student = User(
        clerk_user_id="u_suspended_student",
        email="suspended@sbuniversity.edu",
        full_name="Suspended Student",
        role=UserRole.STUDENT,
        status=UserStatus.SUSPENDED,
    )
    db_session.add(suspended_student)
    await db_session.commit()

    response = await client.post(
        "/admin/courses",
        json={
            "code": "OU-2026-01",
            "title": "OpenUniversity Course",
            "description": "An open course for all active students.",
        },
        headers={"Authorization": "Bearer dev-token-admin-u_admin"},
    )
    assert response.status_code == 201, response.text
    course = response.json()
    assert course["code"] == "OU-2026-01"
    assert course["title"] == "OpenUniversity Course"
    assert course["is_published"] is True
    assert course["enrolled_students"] == 2

    enrollments = (
        await db_session.execute(
            select(Enrollment).where(
                Enrollment.course_id == uuid.UUID(course["id"])
            )
        )
    ).scalars().all()
    assert {enrollment.student_id for enrollment in enrollments} == {
        db_session.test_student1.id,
        db_session.test_student2.id,
    }
    assert all(enrollment.status == EnrollmentStatus.ACTIVE for enrollment in enrollments)

    courses_response = await client.get(
        "/admin/courses",
        headers={"Authorization": "Bearer dev-token-admin-u_admin"},
    )
    assert courses_response.status_code == 200
    assert any(
        item["id"] == course["id"] and item["enrolled_students"] == 2
        for item in courses_response.json()
    )


@pytest.mark.asyncio
async def test_admin_can_create_course_without_enrolling_students(
    client: AsyncClient,
):
    response = await client.post(
        "/admin/courses",
        json={
            "code": "OU-EMPTY",
            "title": "Optional enrollment",
            "enroll_all_active_students": False,
        },
        headers={"Authorization": "Bearer dev-token-admin-u_admin"},
    )
    assert response.status_code == 201, response.text
    assert response.json()["enrolled_students"] == 0


@pytest.mark.asyncio
async def test_teacher_cannot_create_admin_course(client: AsyncClient):
    response = await client.post(
        "/admin/courses",
        json={"code": "OU-NOPE", "title": "Forbidden course"},
        headers={"Authorization": "Bearer dev-token-teacher-u_teacher"},
    )
    assert response.status_code == 403
