import uuid
from typing import Optional
from fastapi import HTTPException, status
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.logging import logger
from app.db.models.user import StudentProfile, TeacherProfile, User, UserRole, UserStatus
from app.repositories.audit_repository import AuditRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserUpdate, VirtualIDCardResponse
from app.services.ranking_service import RankingService


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.audit_repo = AuditRepository(db)
        self.ranking_service = RankingService(db)

    async def get_virtual_id_card(self, user: User) -> VirtualIDCardResponse:
        profile = user.student_profile
        if not profile:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student profile not found")

        dept_name = profile.department.name if profile.department else "General Studies"
        verify_url = f"{settings.FRONTEND_ORIGIN}/verify/student/{profile.qr_token}"

        return VirtualIDCardResponse(
            name=user.full_name,
            student_code=profile.student_code,
            department=dept_name,
            batch_year=profile.batch_year,
            phone=profile.phone,
            photo_url=profile.photo_path or user.avatar_url,
            valid_until=profile.id_valid_until,
            qr_verify_url=verify_url,
            status=user.status.value,
        )

    async def update_profile(self, user: User, data: UserUpdate) -> User:
        if data.full_name is not None:
            user.full_name = data.full_name
        if data.avatar_url is not None:
            user.avatar_url = data.avatar_url

        if user.student_profile and data.phone is not None:
            user.student_profile.phone = data.phone
        if user.student_profile and data.date_of_birth is not None:
            user.student_profile.date_of_birth = data.date_of_birth

        return await self.user_repo.update(user)

    async def change_role(self, user_id: uuid.UUID, new_role: UserRole, admin: User) -> User:
        if admin.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can change user roles")

        target_user = await self.user_repo.get_by_id(user_id)
        if not target_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        old_role = target_user.role
        target_user.role = new_role

        # Sync with Clerk Backend API
        if settings.CLERK_SECRET_KEY and target_user.clerk_user_id:
            try:
                url = f"https://api.clerk.com/v1/users/{target_user.clerk_user_id}/metadata"
                headers = {"Authorization": f"Bearer {settings.CLERK_SECRET_KEY}"}
                payload = {"public_metadata": {"role": new_role.value}}
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.patch(url, headers=headers, json=payload)
                    if resp.status_code != 200:
                        logger.warning("Clerk role sync returned %d: %s", resp.status_code, resp.text)
            except Exception as e:
                logger.error("Failed to sync role with Clerk API: %s", e)

        # Audit log
        await self.audit_repo.log(
            actor_id=admin.id,
            action="user.role_changed",
            entity_type="user",
            entity_id=str(target_user.id),
            metadata={"old_role": old_role.value, "new_role": new_role.value},
        )

        return await self.user_repo.update(target_user)

    async def change_status(self, user_id: uuid.UUID, new_status: UserStatus, admin: User) -> User:
        if admin.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can change user status")

        target_user = await self.user_repo.get_by_id(user_id)
        if not target_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        old_status = target_user.status
        target_user.status = new_status

        await self.audit_repo.log(
            actor_id=admin.id,
            action="user.status_changed",
            entity_type="user",
            entity_id=str(target_user.id),
            metadata={"old_status": old_status.value, "new_status": new_status.value},
        )

        updated_user = await self.user_repo.update(target_user)

        # Refresh ranking (removes from leaderboard if suspended/deleted, or restores if active)
        await self.ranking_service.refresh_student(target_user.id)
        return updated_user
