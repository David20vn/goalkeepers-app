# offer_service.py
from app.schemas.offer_schema import OfferCreate

from app.repositories.offer_repository import OfferRepository
from app.repositories.match_repository import MatchRepository
from app.repositories.goalkeeper_repository import GoalkeeperRepository
from app.repositories.player_repository import PlayerRepository #falta por crear


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
        role = OfferService._get_user_role(current_user)
        user_id = getattr(current_user, "id", None)

        if user_id is None:
            raise ValueError("No se pudo identificar al usuario autenticado.")

        if role == "player":
            return OfferRepository.list_sent_offers_by_player_id(player_id=user_id)

        if role == "goalkeeper":
            goalkeeper = GoalkeeperRepository.get_by_user_id(user_id)
            if not goalkeeper:
                raise ValueError("El arquero no tiene perfil creado.")

            goalkeeper_id = getattr(goalkeeper, "id", None)
            if goalkeeper_id is None:
                raise ValueError("No se pudo identificar el perfil del arquero.")

            return OfferRepository.list_sent_offers_by_goalkeeper_id(goalkeeper_id=goalkeeper_id)

        raise PermissionError("Rol no autorizado para consultar ofertas enviadas.")

    @staticmethod
    def list_received_offers(current_user):
        role = OfferService._get_user_role(current_user)
        user_id = getattr(current_user, "id", None)

        if user_id is None:
            raise ValueError("No se pudo identificar al usuario autenticado.")

        if role == "player":
            return OfferRepository.list_received_offers_by_player_id(player_id=user_id)

        if role == "goalkeeper":
            goalkeeper = GoalkeeperRepository.get_by_user_id(user_id)
            if not goalkeeper:
                raise ValueError("El arquero no tiene perfil creado.")

            goalkeeper_id = getattr(goalkeeper, "id", None)
            if goalkeeper_id is None:
                raise ValueError("No se pudo identificar el perfil del arquero.")

            return OfferRepository.list_received_offers_by_goalkeeper_id(goalkeeper_id=goalkeeper_id)

        raise PermissionError("Rol no autorizado para consultar ofertas recibidas.")

    @staticmethod
    def get_offer_by_id(current_user, offer_id):
        role = OfferService._get_user_role(current_user)
        user_id = getattr(current_user, "id", None)

        if user_id is None:
            raise ValueError("No se pudo identificar al usuario autenticado.")

        offer = OfferRepository.get_offer_by_id(offer_id=offer_id)
        if not offer:
            raise ValueError("La oferta no existe.")

        offer_player_id = OfferService._get_attr(offer, "player_id")
        offer_goalkeeper_id = OfferService._get_attr(offer, "goalkeeper_id")
        sender_role = OfferService._get_attr(offer, "sender_role", "created_by_role")

        # Obtener el perfil del arquero autenticado si aplica
        current_goalkeeper_id = None
        if role == "goalkeeper":
            goalkeeper = GoalkeeperRepository.get_by_user_id(user_id)
            if not goalkeeper:
                raise ValueError("El arquero no tiene perfil creado.")
            current_goalkeeper_id = getattr(goalkeeper, "id", None)
            if current_goalkeeper_id is None:
                raise ValueError("No se pudo identificar el perfil del arquero.")

        # Validación de acceso:
        # - un jugador solo puede ver ofertas relacionadas con sus partidos / donde sea participante
        # - un arquero solo puede ver ofertas donde sea el destinatario o participante
        if role == "player":
            if offer_player_id != user_id:
                raise PermissionError("No tienes permiso para ver esta oferta.")

        elif role == "goalkeeper":
            if offer_goalkeeper_id != current_goalkeeper_id:
                raise PermissionError("No tienes permiso para ver esta oferta.")

        else:
            raise PermissionError("Rol no autorizado para consultar ofertas.")

        return offer

    @staticmethod
    def accept_offer(current_user, offer_id):
        role = OfferService._get_user_role(current_user)
        user_id = getattr(current_user, "id", None)

        if user_id is None:
            raise ValueError("No se pudo identificar al usuario autenticado.")

        if role not in {"player", "goalkeeper"}:
            raise PermissionError("Rol no autorizado para aceptar ofertas.")

        offer = OfferRepository.get_offer_by_id(offer_id=offer_id)
        if not offer:
            raise ValueError("La oferta no existe.")

        offer_status = OfferService._get_attr(offer, "status", "offer_status")
        if offer_status and str(offer_status).lower() != "pending":
            raise ValueError("Solo se pueden aceptar ofertas pendientes.")

        offer_player_id = OfferService._get_attr(offer, "player_id")
        offer_goalkeeper_id = OfferService._get_attr(offer, "goalkeeper_id")
        match_id = OfferService._get_attr(offer, "match_id")

        if match_id is None:
            raise ValueError("La oferta no está asociada a un partido.")

        match = MatchRepository.get_by_id(match_id)
        if not match:
            raise ValueError("El partido asociado a la oferta no existe.")

        match_status = OfferService._get_attr(match, "status", "match_status")
        if match_status and str(match_status).lower() in {"asignado", "assigned"}:
            raise ValueError("El partido ya tiene un arquero asignado.")

        if getattr(match, "goalkeeper_id", None) is not None:
            raise ValueError("El partido ya tiene un arquero asignado.")

        # Verificar que solo el receptor de la oferta pueda aceptarla
        if role == "player":
            if offer_player_id != user_id:
                raise PermissionError("Solo el receptor de la oferta puede aceptarla.")
        elif role == "goalkeeper":
            goalkeeper = GoalkeeperRepository.get_by_user_id(user_id)
            if not goalkeeper:
                raise ValueError("El arquero no tiene perfil creado.")

            current_goalkeeper_id = getattr(goalkeeper, "id", None)
            if current_goalkeeper_id is None:
                raise ValueError("No se pudo identificar el perfil del arquero.")

            if offer_goalkeeper_id != current_goalkeeper_id:
                raise PermissionError("Solo el receptor de la oferta puede aceptarla.")

        # Obtener el arquero que será asignado al partido
        if offer_goalkeeper_id is None:
            raise ValueError("La oferta no tiene arquero asociado.")

        goalkeeper = GoalkeeperRepository.get_by_id(offer_goalkeeper_id)
        if not goalkeeper:
            raise ValueError("El arquero asociado a la oferta no existe.")

        # Operación principal:
        # 1. marcar oferta como aceptada
        # 2. marcar ofertas relacionadas al mismo partido como rechazadas o inactivas
        # 3. asignar arquero al partido
        # 4. cambiar estado del partido a Asignado
        accepted_offer = OfferRepository.accept_offer(offer_id=offer_id)
        MatchRepository.assign_goalkeeper_to_match(
            match_id=match_id,
            goalkeeper_id=offer_goalkeeper_id,
            status="Asignado",
        )
        OfferRepository.reject_other_offers_for_match(match_id=match_id, except_offer_id=offer_id)

        return accepted_offer

    @staticmethod
    def reject_offer(current_user, offer_id):
        role = OfferService._get_user_role(current_user)
        user_id = getattr(current_user, "id", None)

        if user_id is None:
            raise ValueError("No se pudo identificar al usuario autenticado.")

        if role not in {"player", "goalkeeper"}:
            raise PermissionError("Rol no autorizado para rechazar ofertas.")

        offer = OfferRepository.get_offer_by_id(offer_id=offer_id)
        if not offer:
            raise ValueError("La oferta no existe.")

        offer_status = OfferService._get_attr(offer, "status", "offer_status")
        if offer_status and str(offer_status).lower() != "pending":
            raise ValueError("Solo se pueden rechazar ofertas pendientes.")

        offer_player_id = OfferService._get_attr(offer, "player_id")
        offer_goalkeeper_id = OfferService._get_attr(offer, "goalkeeper_id")
        match_id = OfferService._get_attr(offer, "match_id")

        if match_id is None:
            raise ValueError("La oferta no está asociada a un partido.")

        match = MatchRepository.get_by_id(match_id)
        if not match:
            raise ValueError("El partido asociado a la oferta no existe.")

        match_status = OfferService._get_attr(match, "status", "match_status")
        if match_status and str(match_status).lower() in {"asignado", "assigned"}:
            raise ValueError("No se puede rechazar una oferta de un partido ya asignado.")

        # Solo el receptor de la oferta puede rechazarla
        if role == "player":
            if offer_player_id != user_id:
                raise PermissionError("Solo el receptor de la oferta puede rechazarla.")
        elif role == "goalkeeper":
            goalkeeper = GoalkeeperRepository.get_by_user_id(user_id)
            if not goalkeeper:
                raise ValueError("El arquero no tiene perfil creado.")

            current_goalkeeper_id = getattr(goalkeeper, "id", None)
            if current_goalkeeper_id is None:
                raise ValueError("No se pudo identificar el perfil del arquero.")

            if offer_goalkeeper_id != current_goalkeeper_id:
                raise PermissionError("Solo el receptor de la oferta puede rechazarla.")

        rejected_offer = OfferRepository.reject_offer(offer_id=offer_id)
        return rejected_offer