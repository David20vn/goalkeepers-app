from uuid import UUID
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.dependencies.auth_dependencies import get_current_user
from app.schemas.offer_schema import OfferCreate, OfferRead, OfferActionResponse
from app.services.offer_service import OfferService

router = APIRouter(prefix="/offers", tags=["Offers"])


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


async def get_offer_service(
    session: AsyncSession = Depends(get_db),
) -> OfferService:
    return OfferService(session)


@router.post(
    "/",
    response_model=OfferRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an offer",
    description="Create an offer between a player and a goalkeeper. Only the missing party should be provided.",
)
async def create_offer(
    payload: OfferCreate,
    current_user: Any = Depends(get_current_user),
    service: OfferService = Depends(get_offer_service),
):
    try:
        return await service.create_offer(current_user=current_user, payload=payload)
    except Exception as exc:
        raise _map_service_exception(exc)


@router.get(
    "/sent",
    response_model=List[OfferRead],
    summary="List sent offers",
    description="Get all offers sent by the authenticated user.",
)
async def list_sent_offers(
    current_user: Any = Depends(get_current_user),
    service: OfferService = Depends(get_offer_service),
):
    try:
        return await service.list_sent_offers(current_user=current_user)
    except Exception as exc:
        raise _map_service_exception(exc)


@router.get(
    "/received",
    response_model=List[OfferRead],
    summary="List received offers",
    description="Get all offers received by the authenticated user.",
)
async def list_received_offers(
    current_user: Any = Depends(get_current_user),
    service: OfferService = Depends(get_offer_service),
):
    try:
        return await service.list_received_offers(current_user=current_user)
    except Exception as exc:
        raise _map_service_exception(exc)


@router.get(
    "/{offer_id}",
    response_model=OfferRead,
    summary="Get an offer by ID",
    description="Get the details of a specific offer (permission required).",
)
async def get_offer(
    offer_id: UUID,
    current_user: Any = Depends(get_current_user),
    service: OfferService = Depends(get_offer_service),
):
    try:
        return await service.get_offer_by_id(current_user=current_user, offer_id=offer_id)
    except Exception as exc:
        raise _map_service_exception(exc)


@router.put(
    "/{offer_id}/accept",
    response_model=OfferActionResponse,
    summary="Accept an offer",
    description="Accept a pending offer. This assigns the goalkeeper to the match and rejects all other pending offers for that match.",
)
async def accept_offer(
    offer_id: UUID,
    current_user: Any = Depends(get_current_user),
    service: OfferService = Depends(get_offer_service),
):
    try:
        return await service.accept_offer(current_user=current_user, offer_id=offer_id)
    except Exception as exc:
        raise _map_service_exception(exc)


@router.put(
    "/{offer_id}/reject",
    response_model=OfferActionResponse,
    summary="Reject an offer",
    description="Reject a pending offer.",
)
async def reject_offer(
    offer_id: UUID,
    current_user: Any = Depends(get_current_user),
    service: OfferService = Depends(get_offer_service),
):
    try:
        return await service.reject_offer(current_user=current_user, offer_id=offer_id)
    except Exception as exc:
        raise _map_service_exception(exc)