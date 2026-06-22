from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth_dependencies import get_current_user, get_admin_user
from app.schemas.venue_schema import VenueCreate, VenueRead
from app.services.venue_service import VenueService

router = APIRouter( prefix="/venues", tags=["Venues"] )

def _map_service_exception(exc: Exception) -> HTTPException:
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, LookupError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno.")

async def get_venue_service(session: AsyncSession = Depends(get_db)) -> VenueService:
    return VenueService(session)

@router.post(
    "/",
    response_model=VenueRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a venue (admin only)",
)
async def create_venue(
    payload: VenueCreate,
    admin_user = Depends(get_admin_user),   # <-- admin check
    service: VenueService = Depends(get_venue_service),
):
    try:
        return await service.create_venue(payload)
    except Exception as exc:
        raise _map_service_exception(exc)

@router.get(
    "/",
    response_model=List[VenueRead],
    summary="List all venues",
)
async def list_venues(
    service: VenueService = Depends(get_venue_service),
):
    try:
        return await service.list_venues()
    except Exception as exc:
        raise _map_service_exception(exc)

@router.get(
    "/{venue_id}",
    response_model=VenueRead,
    summary="Get venue by ID",
)
async def get_venue(
    venue_id: UUID,
    service: VenueService = Depends(get_venue_service),
):
    try:
        return await service.get_venue(venue_id)
    except Exception as exc:
        raise _map_service_exception(exc)