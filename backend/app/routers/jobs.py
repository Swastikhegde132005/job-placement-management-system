from typing import Annotated
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.deps import get_current_user, require_roles
from app.models.entities import User, UserRole, Company, Job, StudentProfile
from app.schemas.domain import (
    CompanyCreate,
    CompanyResponse,
    JobCreate,
    JobResponse,
    EligibilityResponse
)
from app.services.eligibility import evaluate_eligibility

router = APIRouter(tags=["Companies & Jobs"])

JOBS_CACHE_KEY = "cache:jobs:active"
CACHE_TTL_SECONDS = 300

# ----------------- COMPANIES -----------------

@router.post("/companies", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_in: CompanyCreate,
    current_user: Annotated[User, Depends(require_roles([UserRole.RECRUITER, UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    stmt = select(Company).where(Company.name == company_in.name)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A company with this name already exists"
        )

    company = Company(
        name=company_in.name,
        website=company_in.website,
        created_by=current_user.id
    )
    db.add(company)
    await db.commit()
    await db.refresh(company)
    return company

@router.get("/companies", response_model=list[CompanyResponse])
async def list_companies(
    db: Annotated[AsyncSession, Depends(get_db)]
):
    stmt = select(Company)
    result = await db.execute(stmt)
    return result.scalars().all()

# ----------------- JOBS -----------------

@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def post_job(
    job_in: JobCreate,
    current_user: Annotated[User, Depends(require_roles([UserRole.RECRUITER, UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)]
):
    stmt = select(Company).where(Company.id == job_in.company_id)
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Referenced company does not exist"
        )

    job = Job(**job_in.model_dump())
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Invalidate cached jobs on new posting
    await redis.delete(JOBS_CACHE_KEY)
    return job

@router.get("/jobs", response_model=list[JobResponse])
async def list_active_jobs(
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[aioredis.Redis, Depends(get_redis)]
):
    # 1. Check Redis Cache
    cached_data = await redis.get(JOBS_CACHE_KEY)
    if cached_data:
        jobs_dict = json.loads(cached_data)
        return jobs_dict

    # 2. Cache Miss -> Query Database
    stmt = select(Job).where(Job.is_active == True).order_by(Job.deadline.asc())
    result = await db.execute(stmt)
    jobs = result.scalars().all()

    # Convert to serializable format for Redis
    jobs_response = [JobResponse.model_validate(j).model_dump(mode="json") for j in jobs]
    await redis.setex(JOBS_CACHE_KEY, CACHE_TTL_SECONDS, json.dumps(jobs_response))

    return jobs

@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_details(
    job_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    stmt = select(Job).where(Job.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job

@router.get("/jobs/{job_id}/check-eligibility", response_model=EligibilityResponse)
async def check_student_eligibility(
    job_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_roles([UserRole.STUDENT]))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    job_stmt = select(Job).where(Job.id == job_id)
    job_result = await db.execute(job_stmt)
    job = job_result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    student_stmt = select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    student_result = await db.execute(student_stmt)
    student = student_result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must create a student profile before checking eligibility"
        )

    return evaluate_eligibility(student=student, job=job)
