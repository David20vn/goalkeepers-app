from uuid import UUID
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth_dependencies import get_current_user
from app.schemas.match_schema import MatchCreate, MatchRead, MatchUpdate
from app.services.match_service import MatchService

router = APIRouter(prefix="/matches", tags=["match"])


def _map_service_exception(exc: Exception) -> HTTPException:
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, LookupError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor.")


async def get_match_service(
    session: AsyncSession = Depends(get_db),
) -> MatchService:
    return MatchService(session)


@router.post(
    "/",
    response_model=MatchRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new match",
    description="Create a match (partido) as a player. Initial status is 'Sin arquero'."
)
async def create_match(
    payload: MatchCreate,
    current_user: Any = Depends(get_current_user),
    service: MatchService = Depends(get_match_service),
):
    try:
        return await service.create_match(current_user=current_user, payload=payload)
    except Exception as exc:
        raise _map_service_exception(exc)


@router.get(
    "/my",
    response_model=List[MatchRead],
    status_code=status.HTTP_200_OK,
    summary="List my matches",
    description="List all matches created by the authenticated player."
)
async def list_my_matches(
    current_user: Any = Depends(get_current_user),
    service: MatchService = Depends(get_match_service),
):
    try:
        return await service.list_my_matches(current_user=current_user)
    except Exception as exc:
        raise _map_service_exception(exc)


@router.get(
    "/available",
    response_model=List[MatchRead],
    status_code=status.HTTP_200_OK,
    summary="List available matches",
    description="List all matches that are still without a goalkeeper."
)
async def list_available_matches(
    service: MatchService = Depends(get_match_service),
):
    try:
        return await service.list_available_matches()
    except Exception as exc:
        raise _map_service_exception(exc)


@router.get(
    "/{match_id}",
    response_model=MatchRead,
    status_code=status.HTTP_200_OK,
    summary="Get match by ID"
)
async def get_match(
    match_id: UUID,
    service: MatchService = Depends(get_match_service),
):
    try:
        return await service.get_match(match_id)
    except Exception as exc:
        raise _map_service_exception(exc)


@router.put(
    "/{match_id}",
    response_model=MatchRead,
    status_code=status.HTTP_200_OK,
    summary="Update a match",
    description="Update date, time or location of a match that has no goalkeeper assigned. Only the owner can update it."
)
async def update_match(
    match_id: UUID,
    payload: MatchUpdate,
    current_user: Any = Depends(get_current_user),
    service: MatchService = Depends(get_match_service),
):
    try:
        return await service.update_match(match_id, current_user=current_user, payload=payload)
    except Exception as exc:
        raise _map_service_exception(exc)
    
@router.put(
    "/{match_id}/finalize",
    response_model=MatchRead,
    summary="Finalize a match",
    description="Mark the match as finished. Only the player who created it can do this."
)
async def finalize_match(
    match_id: UUID,
    current_user: Any = Depends(get_current_user),
    service: MatchService = Depends(get_match_service),
):
    try:
        return await service.finalize_match(match_id, current_user)
    except Exception as exc:
        raise _map_service_exception(exc)