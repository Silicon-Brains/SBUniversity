from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.user import UserResponse, UserUpdate
from app.services.storage_service import StorageService
from app.services.user_service import UserService

router = APIRouter(prefix="/me", tags=["Me"])


@router.get("", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("", response_model=UserResponse)
async def update_my_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    return await service.update_profile(current_user, data)


@router.post("/photo", response_model=UserResponse)
async def upload_profile_photo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    contents = await file.read()
    ext = file.filename.split(".")[-1] if file.filename and "." in file.filename else "jpg"
    filename = f"avatars/{current_user.id}.{ext}"

    photo_path = await StorageService.upload_file(filename, contents, file.content_type or "image/jpeg")

    service = UserService(db)
    current_user.avatar_url = photo_path
    if current_user.student_profile:
        current_user.student_profile.photo_path = photo_path

    return await service.update_profile(current_user, UserUpdate(avatar_url=photo_path))
