import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CertificateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    certificate_code: str
    student_id: uuid.UUID
    course_id: uuid.UUID
    final_percentage: float
    issued_at: datetime
    revoked_at: Optional[datetime] = None
    revoked_by: Optional[uuid.UUID] = None
    pdf_path: Optional[str] = None
    course_title: Optional[str] = None
    student_name: Optional[str] = None


class VerifyCertificateResponse(BaseModel):
    is_valid: bool
    certificate_code: str
    student_name: str
    course_title: str
    final_percentage: float
    issued_at: datetime
    revoked_at: Optional[datetime] = None
    revocation_reason: Optional[str] = None


class RevokeCertificateRequest(BaseModel):
    reason: Optional[str] = None
