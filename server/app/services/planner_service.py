import uuid
from typing import Optional
from fastapi import HTTPException
from app.db.models.planner import PlannerEntry, PlannerEntryKind
from app.db.models.user import User
from app.repositories.planner_repository import PlannerRepository
from app.schemas.planner import PlannerEntryCreate, PlannerEntryResponse


class PlannerService:
    def __init__(self, repository: PlannerRepository):
        self.repo = repository

    async def list_entries(
        self, user: User, kind: Optional[PlannerEntryKind] = None
    ) -> list[PlannerEntryResponse]:
        entries = await self.repo.list_for_owner(user.id, kind)
        return [self._response(entry) for entry in entries]

    async def create_entry(
        self, user: User, data: PlannerEntryCreate
    ) -> PlannerEntryResponse:
        if data.kind == PlannerEntryKind.VOICE_NOTE:
            raise HTTPException(
                status_code=422,
                detail="Create voice notes using the audio upload endpoint",
            )
        if data.kind == PlannerEntryKind.EVENT and data.due_at is None:
            raise HTTPException(
                status_code=422, detail="Events require a scheduled date and time"
            )
        if data.kind != PlannerEntryKind.EVENT and data.due_at is not None:
            raise HTTPException(
                status_code=422, detail="Only events can have a scheduled date"
            )
        entry = await self.repo.save(
            PlannerEntry(owner_id=user.id, **data.model_dump())
        )
        return self._response(entry)

    async def get_entry(self, user: User, entry_id: uuid.UUID) -> PlannerEntry:
        entry = await self.repo.get_for_owner(entry_id, user.id)
        if entry is None:
            raise HTTPException(status_code=404, detail="Planner entry not found")
        return entry

    @staticmethod
    def _response(entry: PlannerEntry) -> PlannerEntryResponse:
        return PlannerEntryResponse(
            **{
                field: getattr(entry, field)
                for field in (
                    "id",
                    "owner_id",
                    "kind",
                    "title",
                    "content",
                    "due_at",
                    "is_completed",
                    "color",
                    "shape",
                    "emoji",
                    "audio_mime_type",
                    "audio_size_bytes",
                    "created_at",
                    "updated_at",
                )
            },
            audio_url=(
                f"/planner/entries/{entry.id}/audio"
                if entry.kind == PlannerEntryKind.VOICE_NOTE
                else None
            ),
        )
