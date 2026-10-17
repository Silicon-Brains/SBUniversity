import uuid
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.redis import get_redis_client
from app.db.models.notice import Notice, NoticeAudience, NoticePriority, NoticeStatus
from app.db.models.user import User, UserRole
from app.repositories.course_repository import CourseRepository
from app.repositories.notice_repository import NoticeRepository
from app.schemas.notice import NoticeCreate, NoticeUpdate


class NoticeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.notice_repo = NoticeRepository(db)
        self.course_repo = CourseRepository(db)

    async def invalidate_notice_cache(self):
        redis = await get_redis_client()
        await redis.delete("cache:notices:all", "cache:notices:students", "cache:notices:teachers")

    async def create_notice(self, data: NoticeCreate, author: User) -> Notice:
        if author.role == UserRole.TEACHER:
            if data.audience != NoticeAudience.COURSE or not data.course_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Teachers can only publish notices targeted to their own courses")
            course = await self.course_repo.get_by_id(data.course_id)
            if not course or not await self.course_repo.is_teacher_assigned(
                course.id, author.id
            ):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot post notices to a course taught by another teacher")

        notice = Notice(
            author_id=author.id,
            title=data.title,
            body=data.body,
            audience=data.audience,
            course_id=data.course_id,
            priority=data.priority,
            is_pinned=data.is_pinned if author.role == UserRole.ADMIN else False,
            status=NoticeStatus.PUBLISHED,
            expires_at=data.expires_at,
        )
        saved = await self.notice_repo.create(notice)
        await self.invalidate_notice_cache()
        return saved

    async def update_notice(self, notice_id: uuid.UUID, data: NoticeUpdate, user: User) -> Notice:
        notice = await self.notice_repo.get_by_id(notice_id)
        if not notice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notice not found")

        if user.role != UserRole.ADMIN and notice.author_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        for field, val in data.model_dump(exclude_unset=True).items():
            setattr(notice, field, val)

        saved = await self.notice_repo.update(notice)
        await self.invalidate_notice_cache()
        return saved

    async def delete_notice(self, notice_id: uuid.UUID, user: User) -> None:
        notice = await self.notice_repo.get_by_id(notice_id)
        if not notice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notice not found")

        if user.role != UserRole.ADMIN and notice.author_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        await self.notice_repo.delete(notice)
        await self.invalidate_notice_cache()
