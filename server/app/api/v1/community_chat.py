import uuid
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user
from app.core.rate_limit import RateLimiter
from app.db.models.user import User, UserRole
from app.db.session import get_db
from app.repositories.community_chat_repository import CommunityChatRepository
from app.schemas.chat import (
    CommunityConversationResponse,
    CommunityMessageCreate,
    CommunityMessageResponse,
    CommunityStudentOption,
)
from app.services.community_chat_service import CommunityChatService

router = APIRouter(prefix="/community-chat", tags=["Community Chat"])


def get_service(db: AsyncSession) -> CommunityChatService:
    return CommunityChatService(CommunityChatRepository(db))


@router.get("/conversations", response_model=List[CommunityConversationResponse])
async def list_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_service(db).list_conversations(current_user)


@router.get("/students", response_model=List[CommunityStudentOption])
async def list_students(
    search: str = Query(default="", max_length=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_service(db).list_students(current_user, search)


@router.post(
    "/direct/{student_id}",
    response_model=CommunityConversationResponse,
    dependencies=[Depends(RateLimiter(requests_limit=20, window_seconds=60))],
)
async def start_direct_chat(
    student_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_service(db).start_peer_direct(current_user, student_id)


@router.post(
    "/staff/{staff_role}",
    response_model=CommunityConversationResponse,
    dependencies=[Depends(RateLimiter(requests_limit=10, window_seconds=60))],
)
async def start_staff_chat(
    staff_role: UserRole,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_service(db).start_staff_support(current_user, staff_role)


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=List[CommunityMessageResponse],
)
async def list_messages(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_service(db).list_messages(current_user, conversation_id)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=CommunityMessageResponse,
    dependencies=[Depends(RateLimiter(requests_limit=30, window_seconds=60))],
)
async def send_message(
    conversation_id: uuid.UUID,
    body: CommunityMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_service(db).send_message(
        current_user, conversation_id, body.content
    )
