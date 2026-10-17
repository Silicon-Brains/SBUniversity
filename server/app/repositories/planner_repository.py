import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.planner import PlannerEntry, PlannerEntryKind


class PlannerRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_owner(
        self, owner_id: uuid.UUID, kind: Optional[PlannerEntryKind] = None
    ) -> list[PlannerEntry]:
        stmt = select(PlannerEntry).where(PlannerEntry.owner_id == owner_id)
        if kind is not None:
            stmt = stmt.where(PlannerEntry.kind == kind)
        stmt = stmt.order_by(
            PlannerEntry.is_completed.asc(),
            PlannerEntry.due_at.asc().nulls_last(),
            PlannerEntry.updated_at.desc(),
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def get_for_owner(
        self, entry_id: uuid.UUID, owner_id: uuid.UUID
    ) -> Optional[PlannerEntry]:
        stmt = select(PlannerEntry).where(
            PlannerEntry.id == entry_id, PlannerEntry.owner_id == owner_id
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def save(self, entry: PlannerEntry) -> PlannerEntry:
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def delete(self, entry: PlannerEntry) -> None:
        await self.db.delete(entry)
        await self.db.commit()
