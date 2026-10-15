from datetime import datetime, timedelta, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Course, Enrollment, EnrollmentStatus


@pytest.mark.asyncio
async def test_exam_lifecycle_grading_and_task_points(client: AsyncClient, db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    teacher_id = db_session.test_teacher.id
    student1_id = db_session.test_student1.id

    # 1. Create course & enrollment
    course = Course(
        code="CS-TEST",
        title="Test Computer Science",
        teacher_id=teacher_id,
        is_published=True,
    )
    db_session.add(course)
    await db_session.flush()

    enrollment = Enrollment(
        student_id=student1_id,
        course_id=course.id,
        status=EnrollmentStatus.ACTIVE,
    )
    db_session.add(enrollment)
    await db_session.commit()

    # 2. Teacher creates exam
    exam_payload = {
        "course_id": str(course.id),
        "title": "Algorithms Midterm",
        "instructions": "Attempt all questions",
        "duration_minutes": 30,
        "pass_marks": 5.0,
        "negative_marking": 0.0,
        "max_attempts": 1,
        "start_at": (now - timedelta(hours=1)).isoformat(),
        "end_at": (now + timedelta(hours=5)).isoformat(),
    }
    resp = await client.post("/exams", json=exam_payload, headers={"Authorization": "Bearer dev-token-teacher-u_teacher"})
    assert resp.status_code == 200
    exam_data = resp.json()
    exam_id = exam_data["id"]

    # 3. Teacher adds question
    q_payload = {
        "text": "What is the time complexity of binary search?",
        "marks": 10.0,
        "position": 1,
        "explanation": "Binary search divides the search interval in half each time.",
        "options": [
            {"text": "O(log n)", "is_correct": True, "position": 1},
            {"text": "O(n)", "is_correct": False, "position": 2},
            {"text": "O(n^2)", "is_correct": False, "position": 3},
        ],
    }
    resp = await client.post(f"/exams/{exam_id}/questions", json=q_payload, headers={"Authorization": "Bearer dev-token-teacher-u_teacher"})
    assert resp.status_code == 200
    q_data = resp.json()
    opt_correct_id = next(o["id"] for o in q_data["options"] if o["text"] == "O(log n)")

    # 4. Teacher publishes exam with 50 Task Points
    resp = await client.post(f"/exams/{exam_id}/publish", json={"task_points": 50}, headers={"Authorization": "Bearer dev-token-teacher-u_teacher"})
    assert resp.status_code == 200

    # 5. Student starts attempt
    resp = await client.post(f"/exams/{exam_id}/attempts", headers={"Authorization": "Bearer dev-token-student-u_student1"})
    assert resp.status_code == 200
    attempt_data = resp.json()
    attempt_id = attempt_data["attempt_id"]
    # Check that is_correct is NOT leaked to student
    for q in attempt_data["questions"]:
        for opt in q["options"]:
            assert opt.get("is_correct") is None

    # 6. Student autosaves correct answer
    resp = await client.put(
        f"/attempts/{attempt_id}/answers/{q_data['id']}",
        json={"selected_option_id": opt_correct_id},
        headers={"Authorization": "Bearer dev-token-student-u_student1"},
    )
    assert resp.status_code == 200
    assert resp.json()["saved"] is True

    # 7. Student submits attempt
    resp = await client.post(f"/attempts/{attempt_id}/submit", headers={"Authorization": "Bearer dev-token-student-u_student1"})
    assert resp.status_code == 200
    submit_res = resp.json()
    assert submit_res["score"] == 10.0
    assert submit_res["passed"] is True
    assert submit_res["task_points_awarded"] == 50

    # 8. Check student points summary endpoint
    resp = await client.get("/student/points", headers={"Authorization": "Bearer dev-token-student-u_student1"})
    assert resp.status_code == 200
    pts_res = resp.json()
    assert pts_res["total_points"] == 50
    assert pts_res["tasks_completed"] == 1
