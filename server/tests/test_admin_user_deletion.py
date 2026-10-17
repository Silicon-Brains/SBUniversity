import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models import AuditLog, Course, Notice, User
from app.db.models.notice import NoticeAudience


ADMIN_AUTH = {"Authorization": "Bearer dev-token-admin-u_admin"}


@pytest.mark.asyncio
async def test_admin_deletes_user_from_clerk_and_database(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
):
    calls = []

    class ClerkResponse:
        status_code = 204

    class ClerkClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, traceback):
            return None

        async def delete(self, url: str, headers: dict[str, str]):
            calls.append((url, headers))
            return ClerkResponse()

    monkeypatch.setattr(settings, "CLERK_SECRET_KEY", "test-secret")
    monkeypatch.setattr(
        "app.services.user_service.httpx.AsyncClient",
        lambda timeout: ClerkClient(),
    )

    target_id = db_session.test_student1.id
    notice = Notice(
        author_id=target_id,
        title="Authored material",
        body="Retain this content after account deletion.",
        audience=NoticeAudience.ALL,
    )
    db_session.add(notice)
    await db_session.commit()
    notice_id = notice.id

    response = await client.delete(f"/admin/users/{target_id}", headers=ADMIN_AUTH)

    assert response.status_code == 204, response.text
    assert len(calls) == 1
    assert calls[0][0].endswith("/u_student1")
    assert await db_session.get(User, target_id) is None
    retained_notice = await db_session.get(Notice, notice_id)
    assert retained_notice is not None
    assert retained_notice.author_id is None
    deletion_log = await db_session.scalar(
        select(AuditLog).where(
            AuditLog.action == "user.deleted",
            AuditLog.entity_id == str(target_id),
        )
    )
    assert deletion_log is not None


@pytest.mark.asyncio
async def test_admin_cannot_delete_self_or_teacher_with_assigned_courses(
    client: AsyncClient,
    db_session: AsyncSession,
):
    self_delete = await client.delete(
        f"/admin/users/{db_session.test_admin.id}",
        headers=ADMIN_AUTH,
    )
    assert self_delete.status_code == 400

    course = Course(
        code="ASSIGNED-DELETE-GUARD",
        title="Assigned course",
        teacher_id=db_session.test_teacher.id,
        is_published=True,
    )
    db_session.add(course)
    await db_session.commit()

    teacher_delete = await client.delete(
        f"/admin/users/{db_session.test_teacher.id}",
        headers=ADMIN_AUTH,
    )
    assert teacher_delete.status_code == 409
    assert await db_session.get(User, db_session.test_teacher.id) is not None
