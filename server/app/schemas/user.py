import uuid
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr
from app.db.models.user import UserRole, UserStatus


class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    code: str
    name: str


class StudentProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: uuid.UUID
    student_code: str
    department_id: Optional[uuid.UUID] = None
    department: Optional[DepartmentResponse] = None
    batch_year: Optional[int] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    photo_path: Optional[str] = None
    id_valid_until: Optional[date] = None
    qr_token: str


class TeacherProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: uuid.UUID
    employee_code: str
    department_id: Optional[uuid.UUID] = None
    department: Optional[DepartmentResponse] = None
    designation: Optional[str] = None
    bio: Optional[str] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    clerk_user_id: str
    email: EmailStr
    full_name: str
    avatar_url: Optional[str] = None
    role: UserRole
    status: UserStatus
    created_at: datetime
    student_profile: Optional[StudentProfileResponse] = None
    teacher_profile: Optional[TeacherProfileResponse] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    date_of_birth: Optional[date] = None


class RoleUpdateRequest(BaseModel):
    role: UserRole


class StatusUpdateRequest(BaseModel):
    status: UserStatus


class VirtualIDCardResponse(BaseModel):
    name: str
    student_code: str
    department: Optional[str] = None
    batch_year: Optional[int] = None
    phone: Optional[str] = None
    photo_url: Optional[str] = None
    valid_until: Optional[date] = None
    qr_verify_url: str
    status: str


class UserStatsResponse(BaseModel):
    total: int
    students: int
    teachers: int
    admins: int
