from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session
from app.models.user import UserModel
from app.models.voice import VoiceProfileModel
from app.schemas.voice import (
    VoiceProfileListResponse,
    VoiceProfileRequest,
    VoiceProfileResponse,
    VoiceStyle,
)
from app.services.voice import extract_voice_style

router = APIRouter()


def _model_to_response(profile: VoiceProfileModel) -> VoiceProfileResponse:
    return VoiceProfileResponse(
        id=UUID(profile.id),
        name=profile.name,
        extracted_style=VoiceStyle(**profile.style),
        created_at=profile.created_at,
    )


@router.post("", response_model=VoiceProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_voice_profile(
    payload: VoiceProfileRequest,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> VoiceProfileResponse:
    """Extract and persist a voice profile for the authenticated user."""
    extracted = extract_voice_style(payload.samples)

    profile = VoiceProfileModel(
        user_id=current_user.id,
        name=payload.name,
        style=extracted.model_dump(),
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)

    return _model_to_response(profile)


@router.get("", response_model=VoiceProfileListResponse)
async def list_voice_profiles(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> VoiceProfileListResponse:
    """List all voice profiles belonging to the authenticated user."""
    result = await db.execute(
        select(VoiceProfileModel)
        .where(VoiceProfileModel.user_id == current_user.id)
        .order_by(VoiceProfileModel.created_at.desc())
    )
    profiles = list(result.scalars().all())

    return VoiceProfileListResponse(
        profiles=[_model_to_response(p) for p in profiles],
        total=len(profiles),
    )


@router.get("/{profile_id}", response_model=VoiceProfileResponse)
async def get_voice_profile(
    profile_id: UUID,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> VoiceProfileResponse:
    """Retrieve a single voice profile by ID (owner-scoped)."""
    result = await db.execute(
        select(VoiceProfileModel).where(VoiceProfileModel.id == str(profile_id))
    )
    profile = result.scalar_one_or_none()

    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice profile not found")

    if profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return _model_to_response(profile)


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_voice_profile(
    profile_id: UUID,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Delete a voice profile (owner-scoped)."""
    result = await db.execute(
        select(VoiceProfileModel).where(VoiceProfileModel.id == str(profile_id))
    )
    profile = result.scalar_one_or_none()

    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Voice profile not found")

    if profile.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    await db.delete(profile)
    await db.commit()
