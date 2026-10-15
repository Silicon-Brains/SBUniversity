import uuid
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models.audit import AuditLog


class AuditRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        actor_id: Optional[uuid.UUID],
        action: str,
        entity_type: str,
        entity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        entry = AuditLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_=metadata or {},
            ip_address=ip_address,
        )
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def list_logs(
        self,
        actor_id: Optional[uuid.UUID] = None,
        action: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[AuditLog], int]:
        stmt = select(AuditLog).options(selectinload(AuditLog.actor))
        count_stmt = select(func.count(AuditLog.id))

        if actor_id:
            stmt = stmt.where(AuditLog.actor_id == actor_id)
            count_stmt = count_stmt.where(AuditLog.actor_id == actor_id)
        if action:
            stmt = stmt.where(AuditLog.action == action)
            count_stmt = count_stmt.where(AuditLog.action == action)

        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar_one()

        stmt = stmt.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        res = await self.db.execute(stmt)
        return list(res.scalars().all()), total
