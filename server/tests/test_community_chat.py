from datetime import datetime, timedelta, timezone
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import (
    CommunityConversation,
    CommunityConversationKind,
    CommunityMessage,
)


def auth(user_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer dev-token-{user_id}"}


@pytest.mark.asyncio
async def test_students_can_use_room_and_private_direct_chat(
    client: AsyncClient,
    db_session: AsyncSession,
):
    student_one = auth("student-u_student1")
    student_two = auth("student-u_student2")

    room_list = await client.get("/community-chat/conversations", headers=student_one)
    assert room_list.status_code == 200
    room = next(item for item in room_list.json() if item["is_shared_room"])

    sent_room_message = await client.post(
        f"/community-chat/conversations/{room['id']}/messages",
        json={"content": "Hello, community!"},
        headers=student_one,
    )
    assert sent_room_message.status_code == 200

    room_messages = await client.get(
        f"/community-chat/conversations/{room['id']}/messages",
        headers=student_two,
    )
    assert room_messages.status_code == 200
    assert room_messages.json()[0]["content"] == "Hello, community!"
    assert room_messages.json()[0]["sender_name"] == db_session.test_student1.full_name

    direct = await client.post(
        f"/community-chat/direct/{db_session.test_student2.id}",
        headers=student_one,
    )
    assert direct.status_code == 200
    direct_id = direct.json()["id"]

    duplicate = await client.post(
        f"/community-chat/direct/{db_session.test_student1.id}",
        headers=student_two,
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["id"] == direct_id

    direct_message = await client.post(
        f"/community-chat/conversations/{direct_id}/messages",
        json={"content": "Private message"},
        headers=student_one,
    )
    assert direct_message.status_code == 200
    visible_to_recipient = await client.get(
        f"/community-chat/conversations/{direct_id}/messages",
        headers=student_two,
    )
    assert visible_to_recipient.status_code == 200
    assert visible_to_recipient.json()[0]["content"] == "Private message"

    forbidden = await client.get(
        f"/community-chat/conversations/{direct_id}/messages",
        headers=auth("teacher-u_teacher"),
    )
    assert forbidden.status_code == 404

    duplicate_message = await client.post(
        f"/community-chat/conversations/{direct_id}/messages",
        json={"content": "   "},
        headers=student_one,
    )
    assert duplicate_message.status_code == 422


@pytest.mark.asyncio
async def test_staff_buttons_create_role_scoped_support_inboxes(
    client: AsyncClient,
    db_session: AsyncSession,
):
    student = auth("student-u_student1")
    admin = auth("admin-u_admin")
    teacher = auth("teacher-u_teacher")

    admin_thread = await client.post(
        "/community-chat/staff/admin",
        headers=student,
    )
    teacher_thread = await client.post(
        "/community-chat/staff/teacher",
        headers=student,
    )
    assert admin_thread.status_code == 200
    assert teacher_thread.status_code == 200
    assert admin_thread.json()["kind"] == "admin_support"
    assert teacher_thread.json()["kind"] == "teacher_support"
    assert admin_thread.json()["id"] != teacher_thread.json()["id"]

    wrong_staff_role = await client.get(
        f"/community-chat/conversations/{admin_thread.json()['id']}/messages",
        headers=teacher,
    )
    assert wrong_staff_role.status_code == 404

    message = await client.post(
        f"/community-chat/conversations/{admin_thread.json()['id']}/messages",
        json={"content": "I need help with my account."},
        headers=student,
    )
    assert message.status_code == 200

    admin_inbox = await client.get("/community-chat/conversations", headers=admin)
    teacher_inbox = await client.get("/community-chat/conversations", headers=teacher)
    assert admin_thread.json()["id"] in {item["id"] for item in admin_inbox.json()}
    assert admin_thread.json()["id"] not in {item["id"] for item in teacher_inbox.json()}

    admin_reply = await client.post(
        f"/community-chat/conversations/{admin_thread.json()['id']}/messages",
        json={"content": "An administrator will assist you."},
        headers=admin,
    )
    assert admin_reply.status_code == 200
    assert admin_reply.json()["sender_role"] == "admin"

    student_messages = await client.get(
        f"/community-chat/conversations/{admin_thread.json()['id']}/messages",
        headers=student,
    )
    assert len(student_messages.json()) == 2
    assert student_messages.json()[1]["content"] == "An administrator will assist you."


@pytest.mark.asyncio
async def test_expired_conversations_and_messages_are_deleted(
    client: AsyncClient,
    db_session: AsyncSession,
):
    created = await client.post(
        f"/community-chat/direct/{db_session.test_student2.id}",
        headers=auth("student-u_student1"),
    )
    assert created.status_code == 200
    conversation_id = uuid.UUID(created.json()["id"])

    message = await client.post(
        f"/community-chat/conversations/{conversation_id}/messages",
        json={"content": "This message expires."},
        headers=auth("student-u_student1"),
    )
    assert message.status_code == 200

    conversation = await db_session.get(CommunityConversation, conversation_id)
    assert conversation is not None
    expires_at = conversation.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    assert expires_at > datetime.now(timezone.utc)
    conversation.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    await db_session.commit()

    messages = await client.get(
        f"/community-chat/conversations/{conversation_id}/messages",
        headers=auth("student-u_student1"),
    )
    assert messages.status_code == 404
    db_session.expire_all()
    assert await db_session.get(CommunityConversation, conversation_id) is None
    stored_messages = (
        await db_session.execute(
            select(CommunityMessage).where(
                CommunityMessage.conversation_id == conversation_id
            )
        )
    ).scalars().all()
    assert stored_messages == []


@pytest.mark.asyncio
async def test_students_directory_only_returns_other_active_students(
    client: AsyncClient,
    db_session: AsyncSession,
):
    response = await client.get(
        "/community-chat/students",
        headers=auth("student-u_student1"),
    )
    assert response.status_code == 200
    assert {item["id"] for item in response.json()} == {
        str(db_session.test_student2.id)
    }

    staff_response = await client.get(
        "/community-chat/students",
        headers=auth("teacher-u_teacher"),
    )
    assert staff_response.status_code == 403
