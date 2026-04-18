# offer_service.py

from app.repositories.offer_repository import OfferRepository
from app.schemas.offer_schema import OfferCreate


class OfferService:
    @staticmethod
    def create_offer(current_user, payload: OfferCreate):
        """
        Crea una nueva oferta.
        """
        # TODO: validar rol del usuario
        # TODO: validar datos del payload
        # TODO: verificar reglas de negocio
        # TODO: llamar al repositorio para guardar la oferta
        return OfferRepository.create_offer(current_user=current_user, payload=payload)

    @staticmethod
    def list_sent_offers(current_user):
        """
        Lista las ofertas enviadas por el usuario actual.
        """
        # TODO: validar rol del usuario
        return OfferRepository.list_sent_offers(current_user=current_user)

    @staticmethod
    def list_received_offers(current_user):
        """
        Lista las ofertas recibidas por el usuario actual.
        """
        # TODO: validar rol del usuario
        return OfferRepository.list_received_offers(current_user=current_user)

    @staticmethod
    def get_offer_by_id(current_user, offer_id):
        """
        Obtiene una oferta por su ID.
        """
        # TODO: validar permisos de acceso a la oferta
        return OfferRepository.get_offer_by_id(current_user=current_user, offer_id=offer_id)

    @staticmethod
    def accept_offer(current_user, offer_id):
        """
        Acepta una oferta.
        """
        # TODO: validar que el usuario pueda aceptar esta oferta
        # TODO: validar estado actual de la oferta
        # TODO: actualizar oferta y asignar arquero al partido
        return OfferRepository.accept_offer(current_user=current_user, offer_id=offer_id)

    @staticmethod
    def reject_offer(current_user, offer_id):
        """
        Rechaza una oferta.
        """
        # TODO: validar que el usuario pueda rechazar esta oferta
        # TODO: validar estado actual de la oferta
        return OfferRepository.reject_offer(current_user=current_user, offer_id=offer_id)