from datetime import datetime
from decimal import Decimal
from typing import Optional
import uuid
from pydantic import BaseModel, EmailStr, HttpUrl, ConfigDict
from app.models.entities import UserRole, ApplicationStatus

# --- Auth Schemas ---
class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: UserRole

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: UserRole

# --- Student Profile Schemas ---
class StudentProfileCreate(BaseModel):
    full_name: str
    department: str
    cgpa: Decimal
    tenth_pct: Decimal
    twelfth_pct: Decimal
    active_backlogs: int
    skills: list[str] = []
    resume_url: Optional[HttpUrl] = None

class StudentProfileResponse(StudentProfileCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

# --- Company Schemas ---
class CompanyCreate(BaseModel):
    name: str
    website: Optional[HttpUrl] = None

class CompanyResponse(CompanyCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_by: uuid.UUID
    created_at: datetime

# --- Job Schemas ---
class JobCreate(BaseModel):
    company_id: uuid.UUID
    title: str
    description: str
    min_cgpa: Decimal = Decimal("0.0")
    min_tenth_pct: Decimal = Decimal("0.0")
    min_twelfth_pct: Decimal = Decimal("0.0")
    max_backlogs: int = 0
    required_skills: list[str] = []
    deadline: datetime
    is_active: bool = True

class JobResponse(JobCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime

# --- Application Schemas ---
class ApplicationCreate(BaseModel):
    job_id: uuid.UUID

class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus

class ApplicationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    job_id: uuid.UUID
    status: ApplicationStatus
    applied_at: datetime

# --- Eligibility Check Schema ---
class EligibilityResponse(BaseModel):
    eligible: bool
    reasons: list[str]
