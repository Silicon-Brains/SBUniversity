from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Course, Enrollment, EnrollmentStatus


@pytest.mark.asyncio
async def test_assignment_task_points_and_ranking_flow(client: AsyncClient, db_session: AsyncSession):
    teacher_id = db_session.test_teacher.id
    student1_id = db_session.test_student1.id
    student2_id = db_session.test_student2.id

    # Course & Enrollments
    course = Course(code="AI-TEST", title="Machine Learning Lab", teacher_id=teacher_id, is_published=True)
    db_session.add(course)
    await db_session.flush()

    db_session.add(Enrollment(student_id=student1_id, course_id=course.id, status=EnrollmentStatus.ACTIVE))
    db_session.add(Enrollment(student_id=student2_id, course_id=course.id, status=EnrollmentStatus.ACTIVE))
    await db_session.commit()

    # 1. Teacher creates assignment task with 60 points
    t_payload = {
        "course_id": str(course.id),
        "title": "Neural Network PyTorch Assignment",
        "description": "Implement backpropagation from scratch",
        "points": 60,
    }
    resp = await client.post("/tasks", json=t_payload, headers={"Authorization": "Bearer dev-token-teacher-u_teacher"})
    assert resp.status_code == 200
    task_id = resp.json()["id"]

    # 2. Student 1 submits assignment
    resp = await client.post(
        f"/tasks/{task_id}/complete",
        json={"note": "Repository attached", "url": "https://github.com/student1/pytorch-nn"},
        headers={"Authorization": "Bearer dev-token-student-u_student1"},
    )
    assert resp.status_code == 200
    completion_id = resp.json()["completion_id"]
    assert resp.json()["status"] == "pending_review"

    # 3. Teacher checks reviews
    resp = await client.get("/tasks/reviews", headers={"Authorization": "Bearer dev-token-teacher-u_teacher"})
    assert resp.status_code == 200
    reviews = resp.json()
    assert any(r["id"] == completion_id for r in reviews)

    # 4. Teacher approves completion -> points auto-awarded!
    resp = await client.post(
        f"/tasks/completions/{completion_id}/approve",
        json={"review_note": "Excellent implementation of backprop."},
        headers={"Authorization": "Bearer dev-token-teacher-u_teacher"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"
    assert resp.json()["points_awarded"] == 60

    # 5. Check Live Ranking endpoint
    resp = await client.get("/ranking/top", headers={"Authorization": "Bearer dev-token-student-u_student1"})
    assert resp.status_code == 200
    lb = resp.json()
    assert len(lb["items"]) >= 1
    top_student = lb["items"][0]
    assert top_student["student_id"] == str(student1_id)
    assert top_student["points"] == 60

    # 6. Admin revokes completion
    resp = await client.post(
        f"/admin/progress/tasks/completions/{completion_id}/revoke?reason=Test+Revoke",
        headers={"Authorization": "Bearer dev-token-admin-u_admin"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "revoked"
    assert resp.json()["points_awarded"] == 0

    # 7. Check student points after revoke -> points 0
    resp = await client.get("/student/points", headers={"Authorization": "Bearer dev-token-student-u_student1"})
    assert resp.status_code == 200
    assert resp.json()["total_points"] == 0
