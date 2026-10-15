import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user
from app.core.rate_limit import RateLimiter
from app.db.models.user import User
from app.db.session import get_db
from app.repositories.chat_repository import ChatRepository
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse, ChatSessionResponse
from app.services.ai_service import AIService

router = APIRouter(prefix="/assistant", tags=["Aarsh Intelligence"])


@router.post("/chat", dependencies=[Depends(RateLimiter(requests_limit=20, window_seconds=60))])
async def chat_with_assistant(
    body: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = AIService(db)
    generator = service.chat_stream(
        user=current_user,
        message=body.message,
        session_id=body.session_id,
    )
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_chat_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ChatRepository(db)
    sessions = await repo.list_user_sessions(current_user.id)
    return sessions


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_chat_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ChatRepository(db)
    sess = await repo.get_session(session_id)
    if not sess or sess.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    return sess


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = ChatRepository(db)
    sess = await repo.get_session(session_id)
    if not sess or sess.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    await repo.delete_session(sess)
    return None
