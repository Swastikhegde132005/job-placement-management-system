import uuid
from datetime import datetime, timezone
import enum
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Numeric,
    Integer,
    DateTime,
    ForeignKey,
    Enum,
    UniqueConstraint,
    Index
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from app.core.database import Base

class UserRole(str, enum.Enum):
    STUDENT = "student"
    RECRUITER = "recruiter"
    ADMIN = "admin"

class ApplicationStatus(str, enum.Enum):
    APPLIED = "applied"
    SHORTLISTED = "shortlisted"
    REJECTED = "rejected"
    ACCEPTED = "accepted"

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole, name="user_role_enum"), nullable=False, default=UserRole.STUDENT)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    companies = relationship("Company", back_populates="recruiter", cascade="all, delete-orphan")

class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    department = Column(String(100), nullable=False)
    cgpa = Column(Numeric(4, 2), nullable=False)
    tenth_pct = Column(Numeric(5, 2), nullable=False)
    twelfth_pct = Column(Numeric(5, 2), nullable=False)
    active_backlogs = Column(Integer, default=0, nullable=False)
    skills = Column(ARRAY(String), default=list, nullable=False)
    resume_url = Column(String(500), nullable=True)

    user = relationship("User", back_populates="student_profile")
    applications = relationship("Application", back_populates="student", cascade="all, delete-orphan")

class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False)
    website = Column(String(255), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    recruiter = relationship("User", back_populates="companies")
    jobs = relationship("Job", back_populates="company", cascade="all, delete-orphan")

class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(2000), nullable=False)
    min_cgpa = Column(Numeric(4, 2), default=0.00, nullable=False)
    min_tenth_pct = Column(Numeric(5, 2), default=0.00, nullable=False)
    min_twelfth_pct = Column(Numeric(5, 2), default=0.00, nullable=False)
    max_backlogs = Column(Integer, default=0, nullable=False)
    required_skills = Column(ARRAY(String), default=list, nullable=False)
    deadline = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    company = relationship("Company", back_populates="jobs")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_jobs_active_deadline", "is_active", "deadline"),
    )

class Application(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    status = Column(Enum(ApplicationStatus, name="application_status_enum"), default=ApplicationStatus.APPLIED, nullable=False)
    applied_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    student = relationship("StudentProfile", back_populates="applications")
    job = relationship("Job", back_populates="applications")

    __table_args__ = (
        UniqueConstraint("student_id", "job_id", name="uq_student_job_application"),
        Index("idx_applications_student", "student_id"),
        Index("idx_applications_job_status", "job_id", "status"),
    )
