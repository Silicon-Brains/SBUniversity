import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.db.models.chat import ChatRole


class ChatMessageRequest(BaseModel):
    session_id: Optional[uuid.UUID] = None
    message: str


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    session_id: uuid.UUID
    role: ChatRole
    content: str
    created_at: datetime


class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    user_id: uuid.UUID
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    messages: Optional[List[ChatMessageResponse]] = None
