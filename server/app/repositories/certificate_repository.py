import uuid
from typing import List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models.certificate import Certificate
from app.db.models.course import Course
from app.db.models.user import User


class CertificateRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, certificate_id: uuid.UUID) -> Optional[Certificate]:
        stmt = (
            select(Certificate)
            .options(
                selectinload(Certificate.course),
                selectinload(Certificate.student),
                selectinload(Certificate.revoker),
            )
            .where(Certificate.id == certificate_id)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_code(self, certificate_code: str) -> Optional[Certificate]:
        stmt = (
            select(Certificate)
            .options(
                selectinload(Certificate.course),
                selectinload(Certificate.student),
            )
            .where(Certificate.certificate_code == certificate_code)
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_student_and_course(self, student_id: uuid.UUID, course_id: uuid.UUID) -> Optional[Certificate]:
        stmt = select(Certificate).where(
            Certificate.student_id == student_id,
            Certificate.course_id == course_id,
        )
        res = await self.db.execute(stmt)
        return res.scalar_one_or_none()

    async def list_certificates(
        self,
        student_id: Optional[uuid.UUID] = None,
        course_id: Optional[uuid.UUID] = None,
        include_revoked: bool = True,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Certificate], int]:
        stmt = select(Certificate).options(selectinload(Certificate.course), selectinload(Certificate.student))
        count_stmt = select(func.count(Certificate.id))

        if student_id:
            stmt = stmt.where(Certificate.student_id == student_id)
            count_stmt = count_stmt.where(Certificate.student_id == student_id)
        if course_id:
            stmt = stmt.where(Certificate.course_id == course_id)
            count_stmt = count_stmt.where(Certificate.course_id == course_id)
        if not include_revoked:
            stmt = stmt.where(Certificate.revoked_at.is_(None))
            count_stmt = count_stmt.where(Certificate.revoked_at.is_(None))

        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()

        stmt = stmt.order_by(Certificate.issued_at.desc()).offset((page - 1) * page_size).limit(page_size)
        res = await self.db.execute(stmt)
        return list(res.scalars().all()), total

    async def create(self, certificate: Certificate) -> Certificate:
        self.db.add(certificate)
        await self.db.commit()
        await self.db.refresh(certificate)
        return certificate

    async def update(self, certificate: Certificate) -> Certificate:
        await self.db.commit()
        await self.db.refresh(certificate)
        return certificate
