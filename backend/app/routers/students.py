from typing import Annotated
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.models.entities import User, UserRole, StudentProfile
from app.schemas.domain import StudentProfileCreate, StudentProfileResponse

router = APIRouter(prefix="/students", tags=["Student Profiles"])

@router.post("/me", response_model=StudentProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_my_profile(
    profile_in: StudentProfileCreate,
    current_user: Annotated[User, Depends(require_roles([UserRole.STUDENT]))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    stmt = select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    result = await db.execute(stmt)
    existing_profile = result.scalar_one_or_none()

    if existing_profile:
        # Update existing profile
        for field, value in profile_in.model_dump().items():
            setattr(existing_profile, field, value)
        await db.commit()
        await db.refresh(existing_profile)
        return existing_profile

    # Create new profile
    new_profile = StudentProfile(
        user_id=current_user.id,
        **profile_in.model_dump()
    )
    db.add(new_profile)
    await db.commit()
    await db.refresh(new_profile)
    return new_profile

@router.get("/me", response_model=StudentProfileResponse)
async def get_my_profile(
    current_user: Annotated[User, Depends(require_roles([UserRole.STUDENT]))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    stmt = select(StudentProfile).where(StudentProfile.user_id == current_user.id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found. Please create your profile first."
        )
    return profile

@router.get("/{student_id}", response_model=StudentProfileResponse)
async def get_student_by_id(
    student_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_roles([UserRole.RECRUITER, UserRole.ADMIN]))],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    stmt = select(StudentProfile).where(StudentProfile.id == student_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    return profile
