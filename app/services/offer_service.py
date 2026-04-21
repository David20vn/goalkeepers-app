# offer_service.py
from app.schemas.offer_schema import OfferCreate

from app.repositories.offer_repository import OfferRepository
from app.repositories.match_repository import MatchRepository
from app.repositories.goalkeeper_repository import GoalkeeperRepository
from app.repositories.player_repository import PlayerRepository


class OfferService:

    
    @staticmethod
    def _get_user_role(current_user):
        role = getattr(current_user, "role", None) or getattr(current_user, "user_role", None)
        if not role:
            raise ValueError("El usuario autenticado no tiene un rol válido.")
        return role

    @staticmethod
    def _get_attr(obj, *names):
        for name in names:
            value = getattr(obj, name, None)
            if value is not None:
                return value
        return None

    @staticmethod
    def create_offer(current_user, payload):
        role = OfferService._get_user_role(current_user)
        match_id = getattr(payload, "match_id", None)

        if match_id is None:
            raise ValueError("El campo match_id es obligatorio.")

        match = MatchRepository.get_by_id(match_id)
        if not match:
            raise ValueError("El partido no existe.")

        match_status = OfferService._get_attr(match, "status", "match_status")
        if match_status and str(match_status).lower() in {"asignado", "assigned"}:
            raise ValueError("No se permiten ofertas sobre partidos asignados.")

        if getattr(match, "goalkeeper_id", None) is not None:
            raise ValueError("El partido ya tiene un arquero asignado.")

        # Caso 1: el usuario autenticado es un jugador
        if role == "player":
            goalkeeper_id = OfferService._get_attr(payload, "goalkeeper_id", "recipient_id")
            if goalkeeper_id is None:
                raise ValueError("El jugador debe indicar el arquero destino.")

            goalkeeper = GoalkeeperRepository.get_by_id(goalkeeper_id)
            if not goalkeeper:
                raise ValueError("El arquero no existe.")

            price = OfferService._get_attr(goalkeeper, "fixed_price", "price", "service_price")
            if price is None:
                raise ValueError("El arquero no tiene un precio fijo definido.")

            player_id = getattr(current_user, "id", None)
            if player_id is None:
                raise ValueError("No se pudo identificar al usuario autenticado.")

            # Si el partido tiene dueño, debe coincidir con el jugador autenticado
            match_player_id = getattr(match, "player_id", None)
            if match_player_id is not None and match_player_id != player_id:
                raise PermissionError("No puedes crear ofertas sobre un partido que no te pertenece.")

            offer_data = {
                "match_id": match_id,
                "sender_role": "player",
                "player_id": player_id,
                "goalkeeper_id": goalkeeper_id,
                "price": price,
                "status": "pending",
            }

            return OfferRepository.create_offer(offer_data)

        # Caso 2: el usuario autenticado es un arquero
        if role == "goalkeeper":
            player_id = OfferService._get_attr(payload, "player_id", "recipient_id")
            if player_id is None:
                player_id = getattr(match, "player_id", None)

            if player_id is None:
                raise ValueError("No se pudo determinar el jugador destino de la oferta.")

            player = PlayerRepository.get_by_id(player_id)
            if not player:
                raise ValueError("El jugador no existe.")

            goalkeeper = GoalkeeperRepository.get_by_user_id(getattr(current_user, "id", None))
            if not goalkeeper:
                raise ValueError("El arquero no tiene perfil creado.")

            goalkeeper_id = getattr(goalkeeper, "id", None)
            if goalkeeper_id is None:
                raise ValueError("No se pudo identificar el perfil del arquero.")

            price = OfferService._get_attr(goalkeeper, "fixed_price", "price", "service_price")
            if price is None:
                raise ValueError("El arquero no tiene un precio fijo definido.")

            offer_data = {
                "match_id": match_id,
                "sender_role": "goalkeeper",
                "player_id": player_id,
                "goalkeeper_id": goalkeeper_id,
                "price": price,
                "status": "pending",
            }

            return OfferRepository.create_offer(offer_data)

        raise PermissionError("Rol no autorizado para crear ofertas.")

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