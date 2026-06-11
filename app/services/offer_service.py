from uuid import UUID
from app.repositories.offer_repository import OfferRepository
from app.repositories.match_repository import MatchRepository
from app.repositories.goalkeeper_repository import GoalkeeperRepository
from app.repositories.user_repository import UserRepository

class OfferService:
    def __init__(self, session):
        self.session = session
        self.offer_repo = OfferRepository(session)
        self.match_repo = MatchRepository(session)
        self.goalkeeper_repo = GoalkeeperRepository(session)
        self.user_repo = UserRepository(session)

    @staticmethod
    def _get_user_role(current_user):
        role = getattr(current_user, "role", None) or getattr(current_user, "user_role", None)
        if not role:
            raise ValueError("El usuario autenticado no tiene un rol válido.")
        return role

    async def create_offer(self, current_user, payload):
        role = self._get_user_role(current_user)
        user_id = getattr(current_user, "id", None)
        if not user_id:
            raise ValueError("No se pudo identificar al usuario autenticado.")

        match_id = payload.match_id
        match = await self.match_repo.get_by_id(match_id)
        if not match:
            raise ValueError("El partido no existe.")
        if match.status in ("Asignado", "Finalizado"):
            raise ValueError("El partido ya tiene arquero asignado o finalizó.")

        if role == "player":
            # Player sends offer to a goalkeeper
            goalkeeper_user_id = payload.goalkeeper_id
            if not goalkeeper_user_id:
                raise ValueError("Debes proporcionar el ID del arquero.")
            player_user_id = user_id

            # Verify player owns the match
            if str(match.player_id) != str(player_user_id):
                raise PermissionError("No puedes crear ofertas en partidos que no te pertenecen.")

        elif role == "goalkeeper":
            # Goalkeeper sends offer to a player
            player_user_id = payload.player_id
            if not player_user_id:
                raise ValueError("Debes proporcionar el ID del jugador.")
            goalkeeper_user_id = user_id

            # Verify the match belongs to that player
            if str(match.player_id) != str(player_user_id):
                raise ValueError("El partido no pertenece a ese jugador.")

        else:
            raise PermissionError("Rol no autorizado para crear ofertas.")

        # Verify user roles and existence
        player = await self.user_repo.get_by_id(player_user_id)
        if not player or getattr(player, "role", None) != "player":
            raise ValueError("El jugador no existe o no tiene rol de jugador.")

        goalkeeper = await self.user_repo.get_by_id(goalkeeper_user_id)
        if not goalkeeper or getattr(goalkeeper, "role", None) != "goalkeeper":
            raise ValueError("El arquero no existe o no tiene rol de arquero.")

        # Get goalkeeper's fixed price
        gk_profile = await self.goalkeeper_repo.get_by_user_id(goalkeeper_user_id)
        if not gk_profile:
            raise ValueError("El arquero no tiene perfil creado.")
        price = gk_profile.fixed_price

        # Check for duplicate pending offer
        if await self.offer_repo.exists_pending_offer(match_id, player_user_id, goalkeeper_user_id):
            raise ValueError("Ya existe una oferta pendiente para este partido y arquero.")

        offer_data = {
            "match_id": match_id,
            "player_id": player_user_id,
            "goalkeeper_id": goalkeeper_user_id,
            "sender_role": role,
            "price": price,
            "status": "pending",
        }
        return await self.offer_repo.create(offer_data)

    async def list_sent_offers(self, current_user):
        role = self._get_user_role(current_user)
        user_id = getattr(current_user, "id", None)
        if not user_id:
            raise ValueError("No se pudo identificar al usuario autenticado.")
        return await self.offer_repo.list_sent_by_user(user_id, role)

    async def list_received_offers(self, current_user):
        role = self._get_user_role(current_user)
        user_id = getattr(current_user, "id", None)
        if not user_id:
            raise ValueError("No se pudo identificar al usuario autenticado.")
        return await self.offer_repo.list_received_by_user(user_id, role)

    async def get_offer_by_id(self, current_user, offer_id: UUID):
        role = self._get_user_role(current_user)
        user_id = getattr(current_user, "id", None)
        if not user_id:
            raise ValueError("No se pudo identificar al usuario autenticado.")

        offer = await self.offer_repo.get_by_id(offer_id)
        if not offer:
            raise LookupError("Oferta no encontrada.")

        # Only participants can view the offer
        if role == "player" and str(offer.player_id) != str(user_id):
            raise PermissionError("No tienes permiso para ver esta oferta.")
        if role == "goalkeeper" and str(offer.goalkeeper_id) != str(user_id):
            raise PermissionError("No tienes permiso para ver esta oferta.")

        return offer

    async def accept_offer(self, current_user, offer_id: UUID):
        role = self._get_user_role(current_user)
        user_id = getattr(current_user, "id", None)
        if not user_id:
            raise ValueError("No se pudo identificar al usuario autenticado.")

        offer = await self.offer_repo.get_by_id(offer_id)
        if not offer:
            raise LookupError("Oferta no encontrada.")
        if offer.status != "pending":
            raise ValueError("Solo se pueden aceptar ofertas pendientes.")

        # Only the receiver can accept
        if offer.sender_role == "player":
            receiver_id = offer.goalkeeper_id
            if role != "goalkeeper" or str(user_id) != str(receiver_id):
                raise PermissionError("Solo el arquero receptor puede aceptar esta oferta.")
        else:  # sender_role == "goalkeeper"
            receiver_id = offer.player_id
            if role != "player" or str(user_id) != str(receiver_id):
                raise PermissionError("Solo el jugador receptor puede aceptar esta oferta.")

        # Check match still available
        match = await self.match_repo.get_by_id(offer.match_id)
        if not match:
            raise ValueError("El partido ya no existe.")
        if match.status != "Sin arquero":
            raise ValueError("El partido ya no está disponible.")

        # Assign goalkeeper to match and update offer status
        await self.match_repo.assign_goalkeeper(
            offer.match_id, offer.goalkeeper_id, "Asignado"
        )
        accepted_offer = await self.offer_repo.update_status(offer_id, "accepted")

        # Reject all other pending offers for the same match
        await self.offer_repo.reject_pending_offers_for_match_except(
            offer.match_id, offer_id
        )

        return {
            "id": accepted_offer.id,
            "status": accepted_offer.status,
            "message": "Oferta aceptada y arquero asignado al partido."
        }

    async def reject_offer(self, current_user, offer_id: UUID):
        role = self._get_user_role(current_user)
        user_id = getattr(current_user, "id", None)
        if not user_id:
            raise ValueError("No se pudo identificar al usuario autenticado.")

        offer = await self.offer_repo.get_by_id(offer_id)
        if not offer:
            raise LookupError("Oferta no encontrada.")
        if offer.status != "pending":
            raise ValueError("Solo se pueden rechazar ofertas pendientes.")

        # Only the receiver can reject
        if offer.sender_role == "player":
            receiver_id = offer.goalkeeper_id
            if role != "goalkeeper" or str(user_id) != str(receiver_id):
                raise PermissionError("Solo el arquero receptor puede rechazar esta oferta.")
        else:
            receiver_id = offer.player_id
            if role != "player" or str(user_id) != str(receiver_id):
                raise PermissionError("Solo el jugador receptor puede rechazar esta oferta.")

        rejected_offer = await self.offer_repo.update_status(offer_id, "rejected")
        return {
            "id": rejected_offer.id,
            "status": rejected_offer.status,
            "message": "Oferta rechazada."
        }