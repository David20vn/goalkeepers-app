# app/routers/goalkeeper_router.py

from uuid import UUID
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth_dependencies import get_current_user
from app.schemas.goalkeeper_schema import (
    GoalkeeperCreate,
    GoalkeeperRead,
    GoalkeeperUpdate,
)
from app.services.goalkeeper_service import GoalkeeperService

router = APIRouter( prefix="/goalkeepers", tags=["goalkeeper"])


def _map_service_exception(exc: Exception) -> HTTPException:
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, LookupError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor.")


async def get_goalkeeper_service(
    session: AsyncSession = Depends(get_db),
) -> GoalkeeperService:
    return GoalkeeperService(session)


@router.post(
    "/",
    response_model=GoalkeeperRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create goalkeeper profile",
    description="Create a new goalkeeper profile for the authenticated user. Only users with role 'goalkeeper' can do this.",
)
async def create_profile(
    payload: GoalkeeperCreate,
    current_user: Any = Depends(get_current_user),
    service: GoalkeeperService = Depends(get_goalkeeper_service),
):
    try:
        return await service.create_profile(current_user=current_user, payload=payload)
    except Exception as exc:
        raise _map_service_exception(exc)


@router.get(
    "/me",
    response_model=GoalkeeperRead,
    status_code=status.HTTP_200_OK,
    summary="Get my goalkeeper profile",
    description="Return the goalkeeper profile of the currently authenticated user.",
)
async def get_my_profile(
    current_user: Any = Depends(get_current_user),
    service: GoalkeeperService = Depends(get_goalkeeper_service),
):
    try:
        return await service.get_my_profile(current_user=current_user)
    except Exception as exc:
        raise _map_service_exception(exc)


@router.get(
    "/{goalkeeper_id}",
    response_model=GoalkeeperRead,
    status_code=status.HTTP_200_OK,
    summary="Get a goalkeeper profile by ID",
    description="Return the public profile of a goalkeeper by its identifier.",
)
async def get_profile(
    goalkeeper_id: UUID,
    service: GoalkeeperService = Depends(get_goalkeeper_service),
):
    try:
        return await service.get_profile_by_id(goalkeeper_id)
    except Exception as exc:
        raise _map_service_exception(exc)


@router.put(
    "/me",
    response_model=GoalkeeperRead,
    status_code=status.HTTP_200_OK,
    summary="Update my goalkeeper profile",
    description="Update fields of the authenticated user's goalkeeper profile. Only the profile owner can update it.",
)
async def update_profile(
    payload: GoalkeeperUpdate,
    current_user: Any = Depends(get_current_user),
    service: GoalkeeperService = Depends(get_goalkeeper_service),
):
    try:
        return await service.update_profile(current_user=current_user, payload=payload)
    except Exception as exc:
        raise _map_service_exception(exc)


@router.get(
    "/",
    response_model=List[GoalkeeperRead],
    summary="List goalkeeper profiles with optional filters",
)
async def list_profiles(
    min_rating: Optional[float] = Query(None, ge=0.0, le=5.0, description="Minimum average rating"),
    min_price: Optional[float] = Query(None, ge=0.0, description="Minimum fixed price"),
    max_price: Optional[float] = Query(None, ge=0.0, description="Maximum fixed price"),
    service: GoalkeeperService = Depends(get_goalkeeper_service),
):
    try:
        return await service.list_profiles(
            min_rating=min_rating,
            min_price=min_price,
            max_price=max_price,
        )
    except Exception as exc:
        raise _map_service_exception(exc)