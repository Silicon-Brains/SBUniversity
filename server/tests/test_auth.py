import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_unauthenticated_request_rejected(client: AsyncClient):
    resp = await client.get("/me")
    assert resp.status_code == 401
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_get_me_student(client: AsyncClient):
    resp = await client.get("/me", headers={"Authorization": "Bearer dev-token-student-u_student1"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "student1@sbuniversity.edu"
    assert data["role"] == "student"


@pytest.mark.asyncio
async def test_first_login_provisions_student_profile_without_lazy_load(client: AsyncClient):
    resp = await client.get(
        "/me",
        headers={"Authorization": "Bearer dev-token-student-first_login_regression"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["clerk_user_id"] == "first_login_regression"
    assert data["role"] == "student"
    assert data["student_profile"] is not None
    assert data["student_profile"]["student_code"]


@pytest.mark.asyncio
async def test_first_login_student_code_uses_highest_existing_code(client: AsyncClient, db_session):
    db_session.test_student2.student_profile.student_code = "SBU-2026-0012"
    await db_session.commit()

    resp = await client.get(
        "/me",
        headers={"Authorization": "Bearer dev-token-student-student_code_gap"},
    )

    assert resp.status_code == 200
    assert resp.json()["student_profile"]["student_code"] == "SBU-2026-0013"


@pytest.mark.asyncio
async def test_student_cannot_access_admin_routes(client: AsyncClient):
    resp = await client.get("/admin/users", headers={"Authorization": "Bearer dev-token-student-u_student1"})
    assert resp.status_code == 403
    data = resp.json()
    assert data["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_admin_can_access_admin_routes(client: AsyncClient):
    resp = await client.get("/admin/users", headers={"Authorization": "Bearer dev-token-admin-u_admin"})
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) >= 4


@pytest.mark.asyncio
async def test_admin_change_role_and_student_profile(client: AsyncClient):
    # Find student user
    users_resp = await client.get("/admin/users", headers={"Authorization": "Bearer dev-token-admin-u_admin"})
    student = next(u for u in users_resp.json()["items"] if u["role"] == "student")
    student_id = student["id"]

    # Change role to teacher
    resp1 = await client.patch(
        f"/admin/users/{student_id}/role",
        json={"role": "teacher"},
        headers={"Authorization": "Bearer dev-token-admin-u_admin"},
    )
    assert resp1.status_code == 200
    assert resp1.json()["role"] == "teacher"

    # Change role back to student
    resp2 = await client.patch(
        f"/admin/users/{student_id}/role",
        json={"role": "student"},
        headers={"Authorization": "Bearer dev-token-admin-u_admin"},
    )
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["role"] == "student"
    assert data["student_profile"] is not None


@pytest.mark.asyncio
async def test_update_student_profile(client: AsyncClient):
    resp = await client.patch(
        "/me",
        json={"phone": "+91 99999 88888"},
        headers={"Authorization": "Bearer dev-token-student-u_student1"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["student_profile"] is not None
    assert data["student_profile"]["phone"] == "+91 99999 88888"
