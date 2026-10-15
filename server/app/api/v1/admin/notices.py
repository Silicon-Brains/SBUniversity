import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user, require_role
from app.db.models.notice import NoticeAudience, NoticeStatus
from app.db.models.user import User, UserRole
from app.db.session import get_db
from app.repositories.notice_repository import NoticeRepository
from app.schemas.notice import NoticeResponse
from app.services.notice_service import NoticeService

router = APIRouter(prefix="/notices", tags=["Admin Notices"], dependencies=[Depends(require_role(UserRole.ADMIN))])


@router.get("", response_model=List[NoticeResponse])
async def list_admin_notices(
    audience: Optional[NoticeAudience] = None,
    course_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    repo = NoticeRepository(db)
    notices, _ = await repo.list_notices(audience=audience, course_id=course_id, is_admin=True)
    res = []
    for n in notices:
        nr = NoticeResponse.model_validate(n)
        nr.author_name = n.author.full_name if n.author else "Admin"
        nr.course_title = n.course.title if n.course else None
        res.append(nr)
    return res


@router.post("/{notice_id}/pin", response_model=NoticeResponse)
async def pin_notice(
    notice_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = NoticeRepository(db)
    notice = await repo.get_by_id(notice_id)
    if notice:
        notice.is_pinned = not notice.is_pinned
        await repo.update(notice)
        service = NoticeService(db)
        await service.invalidate_notice_cache()
    return notice


@router.post("/{notice_id}/archive", response_model=NoticeResponse)
async def archive_notice(
    notice_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = NoticeRepository(db)
    notice = await repo.get_by_id(notice_id)
    if notice:
        notice.status = NoticeStatus.ARCHIVED
        await repo.update(notice)
        service = NoticeService(db)
        await service.invalidate_notice_cache()
    return notice
