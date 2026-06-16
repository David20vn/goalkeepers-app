from uuid import UUID
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth_dependencies import get_current_user
from app.schemas.rating import RatingCreate, RatingRead
from app.services.rating_service import RatingService

router = APIRouter(prefix="/ratings", tags=["rating"])

def _map_service_exception(exc: Exception) -> HTTPException:
    if isinstance(exc, ValueError):
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    if isinstance(exc, LookupError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno.")

async def get_rating_service(session: AsyncSession = Depends(get_db)) -> RatingService:
    return RatingService(session)

@router.post("/", response_model=RatingRead, status_code=201)
async def rate_goalkeeper(
    payload: RatingCreate,
    current_user: Any = Depends(get_current_user),
    service: RatingService = Depends(get_rating_service),
):
    try:
        return await service.rate_goalkeeper(current_user, payload)
    except Exception as exc:
        raise _map_service_exception(exc)

@router.get("/goalkeeper/{goalkeeper_id}", response_model=List[RatingRead])
async def get_goalkeeper_ratings(
    goalkeeper_id: UUID,
    service: RatingService = Depends(get_rating_service),
):
    try:
        return await service.get_goalkeeper_ratings(goalkeeper_id)
    except Exception as exc:
        raise _map_service_exception(exc)

@router.get("/goalkeeper/{goalkeeper_id}/average", response_model=float)
async def get_average_rating(
    goalkeeper_id: UUID,
    service: RatingService = Depends(get_rating_service),
):
    try:
        return await service.get_goalkeeper_average(goalkeeper_id)
    except Exception as exc:
        raise _map_service_exception(exc)