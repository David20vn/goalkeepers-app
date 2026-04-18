# app/routers/offer_router.py

from uuid import UUID
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.auth_dependencies import get_current_user
from app.schemas.offer import OfferCreate, OfferRead, OfferActionResponse
from app.services.offer_service import OfferService

router = APIRouter()


def _map_service_exception(exc: Exception) -> HTTPException:
    """
    Convierte excepciones de negocio en respuestas HTTP coherentes.
    """
    if isinstance(exc, ValueError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    if isinstance(exc, PermissionError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )
    if isinstance(exc, LookupError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Error interno del servidor.",
    )


@router.post(
    "/",
    response_model=OfferRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una oferta",
    description=(
        "Crea una oferta entre un jugador y un arquero. "
        "La validación de roles, estado del partido y precio se ejecuta en la capa de servicio."
    ),
)
def create_offer(
    payload: OfferCreate,
    current_user: Any = Depends(get_current_user),
):
    """
    Crea una nueva oferta.
    El service decide si el usuario autenticado puede crearla y cómo debe construirse.
    """
    try:
        return OfferService.create_offer(current_user=current_user, payload=payload)
    except Exception as exc:
        raise _map_service_exception(exc)


@router.get(
    "/sent",
    response_model=List[OfferRead],
    status_code=status.HTTP_200_OK,
    summary="Listar ofertas enviadas",
    description="Devuelve las ofertas enviadas por el usuario autenticado.",
)
def list_sent_offers(
    current_user: Any = Depends(get_current_user),
):
    """
    Retorna las ofertas enviadas por el usuario autenticado.
    """
    try:
        return OfferService.list_sent_offers(current_user=current_user)
    except Exception as exc:
        raise _map_service_exception(exc)


@router.get(
    "/received",
    response_model=List[OfferRead],
    status_code=status.HTTP_200_OK,
    summary="Listar ofertas recibidas",
    description="Devuelve las ofertas recibidas por el usuario autenticado.",
)
def list_received_offers(
    current_user: Any = Depends(get_current_user),
):
    """
    Retorna las ofertas recibidas por el usuario autenticado.
    """
    try:
        return OfferService.list_received_offers(current_user=current_user)
    except Exception as exc:
        raise _map_service_exception(exc)


@router.get(
    "/{offer_id}",
    response_model=OfferRead,
    status_code=status.HTTP_200_OK,
    summary="Obtener una oferta por ID",
    description="Devuelve el detalle de una oferta específica. Solo pueden verla los participantes autorizados.",
)
def get_offer_by_id(
    offer_id: UUID,
    current_user: Any = Depends(get_current_user),
):
    """
    Devuelve la información de una oferta específica.
    El service valida permisos y existencia.
    """
    try:
        return OfferService.get_offer_by_id(current_user=current_user, offer_id=offer_id)
    except Exception as exc:
        raise _map_service_exception(exc)


@router.put(
    "/{offer_id}/accept",
    response_model=OfferActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Aceptar oferta",
    description=(
        "Acepta una oferta y asigna el arquero al partido en una sola operación. "
        "Solo el receptor de la oferta puede ejecutarlo."
    ),
)
def accept_offer(
    offer_id: UUID,
    current_user: Any = Depends(get_current_user),
):
    """
    Acepta una oferta y activa la asignación del arquero.
    """
    try:
        return OfferService.accept_offer(current_user=current_user, offer_id=offer_id)
    except Exception as exc:
        raise _map_service_exception(exc)


@router.put(
    "/{offer_id}/reject",
    response_model=OfferActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Rechazar oferta",
    description="Rechaza una oferta recibida por el usuario autenticado.",
)
def reject_offer(
    offer_id: UUID,
    current_user: Any = Depends(get_current_user),
):
    """
    Rechaza una oferta.
    Solo el receptor puede rechazarla.
    """
    try:
        return OfferService.reject_offer(current_user=current_user, offer_id=offer_id)
    except Exception as exc:
        raise _map_service_exception(exc)