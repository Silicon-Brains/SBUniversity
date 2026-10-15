from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.analytics import PublicStatsResponse
from app.schemas.certificate import VerifyCertificateResponse
from app.services.analytics_service import AnalyticsService
from app.services.certificate_service import CertificateService

router = APIRouter(prefix="/public", tags=["Public"])


@router.get("/stats", response_model=PublicStatsResponse)
async def get_public_stats(db: AsyncSession = Depends(get_db)):
    service = AnalyticsService(db)
    return await service.get_public_stats()


@router.get("/verify/certificate/{code}", response_model=VerifyCertificateResponse)
async def verify_certificate(code: str, db: AsyncSession = Depends(get_db)):
    service = CertificateService(db)
    return await service.verify_certificate(code)


@router.get("/verify/student/{qr_token}")
async def verify_student(qr_token: str, db: AsyncSession = Depends(get_db)):
    user_repo = UserRepository(db)
    profile = await user_repo.get_student_by_qr_token(qr_token)
    if not profile or not profile.user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student record not found or invalid QR token")

    dept_name = profile.department.name if profile.department else "General Studies"
    return {
        "is_valid": profile.user.status.value == "active",
        "student_name": profile.user.full_name,
        "student_code": profile.student_code,
        "department": dept_name,
        "batch_year": profile.batch_year,
        "valid_until": profile.id_valid_until.isoformat() if profile.id_valid_until else None,
        "status": profile.user.status.value,
    }
