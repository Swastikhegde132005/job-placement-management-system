from typing import Annotated
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.entities import (
    User,
    UserRole,
    StudentProfile,
    Job,
    Application,
    ApplicationStatus
)
from app.schemas.domain import (
    ApplicationCreate,
    ApplicationStatusUpdate,
    ApplicationResponse
)
from app.services.eligibility import evaluate_eligibility

router = APIRouter(prefix="/applications", tags=["Applications"])

@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def apply_for_job(
    app_in: ApplicationCreate,
    current_user: Annotated[User, Depends(require_roles([UserRole.STUDENT]))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # 1. Fetch student profile
    student_stmt = select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    student_res = await db.execute(student_stmt)
    student = student_res.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must create your student profile before applying for jobs"
        )

    # 2. Fetch job and check deadline/active status
    job_stmt = select(Job).where(Job.id == app_in.job_id)
    job_res = await db.execute(job_stmt)
    job = job_res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if not job.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This job is no longer accepting applications")

    if datetime.now(timezone.utc) > job.deadline:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Application deadline for this job has passed")

    # 3. Check rule-based eligibility
    eligibility = evaluate_eligibility(student=student, job=job)
    if not eligibility.eligible:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "You are not eligible for this position",
                "reasons": eligibility.reasons
            }
        )

    # 4. Attempt application creation (database handles unique constraint)
    new_application = Application(
        student_id=student.id,
        job_id=job.id,
        status=ApplicationStatus.APPLIED
    )
    db.add(new_application)

    try:
        await db.commit()
        await db.refresh(new_application)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already applied for this position"
        )

    return new_application

@router.get("/my", response_model=list[ApplicationResponse])
async def get_my_applications(
    current_user: Annotated[User, Depends(require_roles([UserRole.STUDENT]))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    student_stmt = select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    student_res = await db.execute(student_stmt)
    student = student_res.scalar_one_or_none()
    if not student:
        return []

    app_stmt = select(Application).where(Application.student_id == student.id).order_by(Application.applied_at.desc())
    app_res = await db.execute(app_stmt)
    return app_res.scalars().all()

@router.get("/job/{job_id}", response_model=list[ApplicationResponse])
async def get_job_applications(
    job_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_roles([UserRole.RECRUITER, UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    app_stmt = select(Application).where(Application.job_id == job_id).order_by(Application.applied_at.desc())
    app_res = await db.execute(app_stmt)
    return app_res.scalars().all()

@router.patch("/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    application_id: uuid.UUID,
    status_update: ApplicationStatusUpdate,
    current_user: Annotated[User, Depends(require_roles([UserRole.RECRUITER, UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    app_stmt = select(Application).where(Application.id == application_id)
    app_res = await db.execute(app_stmt)
    application = app_res.scalar_one_or_none()
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    application.status = status_update.status
    await db.commit()
    await db.refresh(application)
    return application
