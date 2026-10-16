import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_admin_published_student_notice_is_visible_to_students(client: AsyncClient):
    create_response = await client.post(
        "/notices",
        json={
            "title": "Student Notice Visibility Test",
            "body": "This notice should be available on the student notice board.",
            "audience": "students",
            "priority": "important",
            "is_pinned": True,
        },
        headers={"Authorization": "Bearer dev-token-admin-u_admin"},
    )

    assert create_response.status_code == 200
    created_notice = create_response.json()
    assert created_notice["status"] == "published"

    admin_list_response = await client.get(
        "/admin/notices",
        headers={"Authorization": "Bearer dev-token-admin-u_admin"},
    )
    assert admin_list_response.status_code == 200
    assert any(item["id"] == created_notice["id"] for item in admin_list_response.json())

    student_list_response = await client.get(
        "/notices",
        headers={"Authorization": "Bearer dev-token-student-u_student1"},
    )
    assert student_list_response.status_code == 200
    student_notices = student_list_response.json()
    visible_notice = next(item for item in student_notices if item["id"] == created_notice["id"])
    assert visible_notice["audience"] == "students"
    assert visible_notice["title"] == "Student Notice Visibility Test"
