import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models.chat import (
    CommunityConversation,
    CommunityConversationKind,
    CommunityMessage,
)
from app.db.models.user import User, UserRole, UserStatus

COMMUNITY_CHAT_LIFETIME = timedelta(hours=10)


class CommunityChatRepository:
    ROOM_KEY = "student-community-room"

    def __init__(self, db: AsyncSession):
        self.db = db

    async def delete_expired(self, now: Optional[datetime] = None) -> int:
        cutoff = now or datetime.now(timezone.utc)
        expired_ids = list(
            (
                await self.db.execute(
                    select(CommunityConversation.id).where(
                        CommunityConversation.expires_at <= cutoff
                    )
                )
            )
            .scalars()
            .all()
        )
        if expired_ids:
            await self.db.execute(
                delete(CommunityMessage).where(
                    CommunityMessage.conversation_id.in_(expired_ids)
                )
            )
            await self.db.execute(
                delete(CommunityConversation)
                .where(CommunityConversation.id.in_(expired_ids))
                .execution_options(synchronize_session=False)
            )
            await self.db.commit()
        return len(expired_ids)

    async def get_or_create_student_room(self) -> CommunityConversation:
        stmt = select(CommunityConversation).where(
            CommunityConversation.room_key == self.ROOM_KEY
        )
        conversation = (await self.db.execute(stmt)).scalar_one_or_none()
        if conversation:
            return conversation

        now = datetime.now(timezone.utc)
        conversation = CommunityConversation(
            kind=CommunityConversationKind.STUDENT_ROOM,
            room_key=self.ROOM_KEY,
            expires_at=now + COMMUNITY_CHAT_LIFETIME,
        )
        self.db.add(conversation)
        try:
            await self.db.commit()
            await self.db.refresh(conversation)
            return conversation
        except IntegrityError:
            await self.db.rollback()
            existing = (await self.db.execute(stmt)).scalar_one_or_none()
            if existing is None:
                raise
            return existing

    async def find_peer_direct(
        self, peer_one_id: uuid.UUID, peer_two_id: uuid.UUID
    ) -> Optional[CommunityConversation]:
        stmt = select(CommunityConversation).where(
            CommunityConversation.kind == CommunityConversationKind.PEER_DIRECT,
            CommunityConversation.peer_one_id == peer_one_id,
            CommunityConversation.peer_two_id == peer_two_id,
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def find_support(
        self, student_id: uuid.UUID, kind: CommunityConversationKind
    ) -> Optional[CommunityConversation]:
        stmt = select(CommunityConversation).where(
            CommunityConversation.requester_student_id == student_id,
            CommunityConversation.kind == kind,
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def save_conversation(
        self, conversation: CommunityConversation
    ) -> CommunityConversation:
        self.db.add(conversation)
        try:
            await self.db.commit()
            await self.db.refresh(conversation)
            return conversation
        except IntegrityError:
            await self.db.rollback()
            if conversation.kind == CommunityConversationKind.PEER_DIRECT:
                existing = await self.find_peer_direct(
                    conversation.peer_one_id, conversation.peer_two_id
                )
            else:
                existing = await self.find_support(
                    conversation.requester_student_id, conversation.kind
                )
            if existing is None:
                raise
            return existing

    async def list_for_student(self, student_id: uuid.UUID) -> List[CommunityConversation]:
        stmt = (
            select(CommunityConversation)
            .where(
                (CommunityConversation.room_key == self.ROOM_KEY)
                | (
                    (CommunityConversation.kind == CommunityConversationKind.PEER_DIRECT)
                    & (
                        (CommunityConversation.peer_one_id == student_id)
                        | (CommunityConversation.peer_two_id == student_id)
                    )
                )
                | (CommunityConversation.requester_student_id == student_id)
            )
            .order_by(CommunityConversation.updated_at.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def list_for_staff(
        self, kind: CommunityConversationKind
    ) -> List[CommunityConversation]:
        stmt = (
            select(CommunityConversation)
            .where(CommunityConversation.kind == kind)
            .order_by(CommunityConversation.updated_at.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def list_last_messages(
        self, conversations: List[CommunityConversation]
    ) -> dict[uuid.UUID, CommunityMessage]:
        if not conversations:
            return {}
        latest_time = (
            select(
                CommunityMessage.conversation_id.label("conversation_id"),
                func.max(CommunityMessage.created_at).label("created_at"),
            )
            .where(
                CommunityMessage.conversation_id.in_(
                    [conversation.id for conversation in conversations]
                )
            )
            .group_by(CommunityMessage.conversation_id)
            .subquery()
        )
        stmt = (
            select(CommunityMessage)
            .join(
                latest_time,
                (CommunityMessage.conversation_id == latest_time.c.conversation_id)
                & (CommunityMessage.created_at == latest_time.c.created_at),
            )
        )
        messages = (await self.db.execute(stmt)).scalars().all()
        return {message.conversation_id: message for message in messages}

    async def get_users(self, user_ids: set[uuid.UUID]) -> dict[uuid.UUID, User]:
        if not user_ids:
            return {}
        users = (
            await self.db.execute(select(User).where(User.id.in_(user_ids)))
        ).scalars().all()
        return {user.id: user for user in users}

    async def get_accessible_conversation(
        self, conversation_id: uuid.UUID
    ) -> Optional[CommunityConversation]:
        stmt = select(CommunityConversation).where(
            CommunityConversation.id == conversation_id
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def list_messages(
        self, conversation_id: uuid.UUID, limit: int = 100
    ) -> List[CommunityMessage]:
        stmt = (
            select(CommunityMessage)
            .options(selectinload(CommunityMessage.sender))
            .where(CommunityMessage.conversation_id == conversation_id)
            .order_by(CommunityMessage.created_at.desc(), CommunityMessage.id.desc())
            .limit(limit)
        )
        return list(reversed((await self.db.execute(stmt)).scalars().all()))

    async def add_message(
        self,
        conversation: CommunityConversation,
        sender_id: uuid.UUID,
        content: str,
    ) -> CommunityMessage:
        now = datetime.now(timezone.utc)
        message = CommunityMessage(
            conversation_id=conversation.id,
            sender_id=sender_id,
            content=content,
            created_at=now,
        )
        conversation.updated_at = now
        conversation.expires_at = now + COMMUNITY_CHAT_LIFETIME
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        stmt = (
            select(CommunityMessage)
            .options(selectinload(CommunityMessage.sender))
            .where(CommunityMessage.id == message.id)
        )
        return (await self.db.execute(stmt)).scalar_one()

    async def list_active_students(
        self, current_student_id: uuid.UUID, search: str = ""
    ) -> List[User]:
        stmt = (
            select(User)
            .where(
                User.id != current_student_id,
                User.role == UserRole.STUDENT,
                User.status == UserStatus.ACTIVE,
            )
            .order_by(User.full_name.asc())
            .limit(50)
        )
        if search.strip():
            stmt = stmt.where(User.full_name.ilike(f"%{search.strip()}%"))
        return list((await self.db.execute(stmt)).scalars().all())
