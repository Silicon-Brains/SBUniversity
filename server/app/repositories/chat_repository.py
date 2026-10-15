import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models.chat import ChatMessage, ChatRole, ChatSession


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_session(self, session_id: uuid.UUID) -> Optional[ChatSession]:
        stmt = select(ChatSession).options(selectinload(ChatSession.messages)).where(ChatSession.id == session_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_user_sessions(self, user_id: uuid.UUID) -> List[ChatSession]:
        stmt = (
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
        )
        res = await self.db.execute(stmt)
        return list(res.scalars().all())

    async def create_session(self, session: ChatSession) -> ChatSession:
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def add_message(self, session_id: uuid.UUID, role: ChatRole, content: str) -> ChatMessage:
        msg = ChatMessage(session_id=session_id, role=role, content=content)
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def delete_session(self, session: ChatSession) -> None:
        await self.db.delete(session)
        await self.db.commit()
