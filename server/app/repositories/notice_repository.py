import uuid
from typing import List, Optional, Tuple
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models.course import Course
from app.db.models.notice import Notice, NoticeAudience, NoticeStatus
from app.db.models.user import User


class NoticeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, notice_id: uuid.UUID) -> Optional[Notice]:
        stmt = select(Notice).options(selectinload(Notice.author), selectinload(Notice.course)).where(Notice.id == notice_id)
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_notices(
        self,
        audience: Optional[NoticeAudience] = None,
        course_id: Optional[uuid.UUID] = None,
        enrolled_course_ids: Optional[List[uuid.UUID]] = None,
        is_teacher: bool = False,
        is_admin: bool = False,
        status: NoticeStatus = NoticeStatus.PUBLISHED,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Notice], int]:
        stmt = select(Notice).options(selectinload(Notice.author), selectinload(Notice.course))
        count_stmt = select(func.count(Notice.id))

        if not is_admin:
            stmt = stmt.where(Notice.status == status)
            count_stmt = count_stmt.where(Notice.status == status)
            # Not expired
            stmt = stmt.where(or_(Notice.expires_at.is_(None), Notice.expires_at > func.now()))
            count_stmt = count_stmt.where(or_(Notice.expires_at.is_(None), Notice.expires_at > func.now()))

            # Role audience filtering
            audience_conditions = [Notice.audience == NoticeAudience.ALL]
            if is_teacher:
                audience_conditions.append(Notice.audience == NoticeAudience.TEACHERS)
            else:
                audience_conditions.append(Notice.audience == NoticeAudience.STUDENTS)

            if enrolled_course_ids:
                audience_conditions.append((Notice.audience == NoticeAudience.COURSE) & (Notice.course_id.in_(enrolled_course_ids)))

            stmt = stmt.where(or_(*audience_conditions))
            count_stmt = count_stmt.where(or_(*audience_conditions))
        else:
            if audience:
                stmt = stmt.where(Notice.audience == audience)
                count_stmt = count_stmt.where(Notice.audience == audience)
            if course_id:
                stmt = stmt.where(Notice.course_id == course_id)
                count_stmt = count_stmt.where(Notice.course_id == course_id)

        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()

        # Pinned first, then published_at desc
        stmt = stmt.order_by(Notice.is_pinned.desc(), Notice.published_at.desc()).offset((page - 1) * page_size).limit(page_size)
        res = await self.db.execute(stmt)
        return list(res.scalars().all()), total

    async def create(self, notice: Notice) -> Notice:
        self.db.add(notice)
        await self.db.commit()
        await self.db.refresh(notice)
        return notice

    async def update(self, notice: Notice) -> Notice:
        await self.db.commit()
        await self.db.refresh(notice)
        return notice

    async def delete(self, notice: Notice) -> None:
        await self.db.delete(notice)
        await self.db.commit()
