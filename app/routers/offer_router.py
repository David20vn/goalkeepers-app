# app/routers/offer_router.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Any

from app.dependencies.auth_dependencies import get_current_user
from app.schemas.offer import (
    OfferCreate,
    OfferRead,
    OfferActionResponse,
)
from app.services.offer_service import OfferService

router = APIRouter(tags=["Offers"])


@router.post(
    "/",
    response_model=OfferRead,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una oferta",
    description=(
        "Crea una oferta entre un jugador y un arquero. "
        "El precio debe salir del perfil del arquero y la lógica de validación "
        "se ejecuta en la capa de servicio."
    ),
)
def create_offer( payload: OfferCreate, current_user: Any = Depends(get_current_user), ):
    """
    Crea una nueva oferta.
    Puede ser iniciada por un jugador o por un arquero, según las reglas del sistema.
    """
    try:
        return OfferService.create_offer(current_user=current_user, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get(
    "/sent",
    response_model=List[OfferRead],
    summary="Listar ofertas enviadas",
    description="Devuelve las ofertas que el usuario autenticado ha enviado.",
)
def list_sent_offers( current_user: Any = Depends(get_current_user), ):
    """
    Retorna las ofertas que el usuario autenticado ha enviado.
    """
    try:
        return OfferService.list_sent_offers(current_user=current_user)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get(
    "/received",
    response_model=List[OfferRead],
    summary="Listar ofertas recibidas",
    description="Devuelve las ofertas que el usuario autenticado ha recibido.",
)
def list_received_offers( current_user: Any = Depends(get_current_user), ):
    """
    Retorna las ofertas que el usuario autenticado ha recibido.
    """
    try:
        return OfferService.list_received_offers(current_user=current_user)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.get(
    "/{offer_id}",
    response_model=OfferRead,
    summary="Obtener una oferta por ID",
    description="Devuelve el detalle de una oferta específica.",
)
def get_offer_by_id( offer_id: int, current_user: Any = Depends(get_current_user), ):
    """
    Devuelve la información de una oferta específica.
    La capa de servicio debe validar que el usuario tenga permiso para verla.
    """
    try:
        return OfferService.get_offer_by_id(current_user=current_user, offer_id=offer_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.put(
    "/{offer_id}/accept",
    response_model=OfferActionResponse,
    summary="Aceptar oferta",
    description=(
        "Acepta una oferta y dispara la asignación del arquero al partido. "
        "La transacción debe evitar doble asignación."
    ),
)
def accept_offer( offer_id: int, current_user: Any = Depends(get_current_user), ):
    """
    Acepta una oferta.
    La capa de servicio debe ejecutar la transacción completa:
    validar estado, asignar arquero, marcar oferta como aceptada y rechazar las demás.
    """
    try:
        return OfferService.accept_offer(current_user=current_user, offer_id=offer_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


@router.put(
    "/{offer_id}/reject",
    response_model=OfferActionResponse,
    summary="Rechazar oferta",
    description="Rechaza una oferta recibida por el usuario autenticado.",
)
def reject_offer( offer_id: int, current_user: Any = Depends(get_current_user), ):
    """
    Rechaza una oferta.
    """
    try:
        return OfferService.reject_offer(current_user=current_user, offer_id=offer_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))