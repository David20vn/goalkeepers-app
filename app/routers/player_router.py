# app/routers/player_router.py

from uuid import UUID
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth_dependencies import get_current_user
from app.schemas.player_schema import PlayerCreate, PlayerRead, PlayerUpdate
from app.services.player_service import PlayerService

router = APIRouter( prefix="/players", tags=["player"])


def _map_service_exception(exc: Exception) -> HTTPException:
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, LookupError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Error interno del servidor.",
    )


async def get_player_service(
    session: AsyncSession = Depends(get_db),
) -> PlayerService:
    return PlayerService(session)


@router.post(
    "/",
    response_model=PlayerRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create player profile",
    description="Create a new player profile for the authenticated user. Only users with role 'player' can do this.",
)
async def create_profile(
    payload: PlayerCreate,
    current_user: Any = Depends(get_current_user),
    service: PlayerService = Depends(get_player_service),
):
    try:
        return await service.create_profile(current_user=current_user, payload=payload)
    except Exception as exc:
        raise _map_service_exception(exc)


@router.get(
    "/me",
    response_model=PlayerRead,
    status_code=status.HTTP_200_OK,
    summary="Get my player profile",
    description="Return the player profile of the currently authenticated user.",
)
async def get_my_profile(
    current_user: Any = Depends(get_current_user),
    service: PlayerService = Depends(get_player_service),
):
    try:
        return await service.get_my_profile(current_user=current_user)
    except Exception as exc:
        raise _map_service_exception(exc)


@router.get(
    "/{player_id}",
    response_model=PlayerRead,
    status_code=status.HTTP_200_OK,
    summary="Get a player profile by ID",
    description="Return the public profile of a player by its identifier.",
)
async def get_profile(
    player_id: UUID,
    service: PlayerService = Depends(get_player_service),
):
    try:
        return await service.get_profile_by_id(player_id)
    except Exception as exc:
        raise _map_service_exception(exc)


@router.put(
    "/me",
    response_model=PlayerRead,
    status_code=status.HTTP_200_OK,
    summary="Update my player profile",
    description="Update fields of the authenticated user's player profile. Only the profile owner can update it.",
)
async def update_profile(
    payload: PlayerUpdate,
    current_user: Any = Depends(get_current_user),
    service: PlayerService = Depends(get_player_service),
):
    try:
        return await service.update_profile(current_user=current_user, payload=payload)
    except Exception as exc:
        raise _map_service_exception(exc)


@router.get(
    "/",
    response_model=List[PlayerRead],
    status_code=status.HTTP_200_OK,
    summary="List player profiles",
    description="Get a list of player profiles.",
)
async def list_profiles(
    service: PlayerService = Depends(get_player_service),
):
    try:
        return await service.list_profiles()
    except Exception as exc:
        raise _map_service_exception(exc)