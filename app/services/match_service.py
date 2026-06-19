from uuid import UUID
from app.repositories.match_repository import MatchRepository
from app.repositories.offer_repository import OfferRepository
from app.models.match import Match


class MatchService:
    def __init__(self, session):
        self.session = session
        self.match_repo = MatchRepository(session)
        self.offer_repo = OfferRepository(session)

    @staticmethod
    def _get_user_role(current_user):
        role = getattr(current_user, "role", None) or getattr(current_user, "user_role", None)
        if not role:
            raise ValueError("El usuario autenticado no tiene un rol válido.")
        return role

    async def create_match(self, current_user, payload):
        role = self._get_user_role(current_user)
        if role != "player":
            raise PermissionError("Solo los jugadores pueden crear partidos.")

        user_id = getattr(current_user, "id", None)
        if user_id is None:
            raise ValueError("No se pudo identificar al usuario autenticado.")

        data = {
            "player_id": user_id,
            "date": payload.date,
            "time": payload.time,
            "location": payload.location,
            "status": "Sin arquero"
        }
        return await self.match_repo.create(data)

    async def get_match(self, match_id: UUID):
        match = await self.match_repo.get_by_id(match_id)
        if not match:
            raise LookupError("Partido no encontrado.")
        return match

    async def list_my_matches(self, current_user):
        role = self._get_user_role(current_user)
        if role != "player":
            raise PermissionError("Solo los jugadores pueden ver sus partidos.")
        user_id = getattr(current_user, "id", None)
        if user_id is None:
            raise ValueError("No se pudo identificar al usuario autenticado.")
        return await self.match_repo.list_by_player(user_id)

    async def list_available_matches(self):
        return await self.match_repo.list_available()

    async def update_match(self, match_id: UUID, current_user, payload):
        role = self._get_user_role(current_user)
        if role != "player":
            raise PermissionError("Solo los jugadores pueden actualizar partidos.")

        match = await self.match_repo.get_by_id(match_id)
        if not match:
            raise LookupError("Partido no encontrado.")

        user_id = getattr(current_user, "id", None)
        if str(match.player_id) != str(user_id):
            raise PermissionError("Solo el creador del partido puede modificarlo.")

        if match.status != "Sin arquero":
            raise ValueError("Solo se pueden modificar partidos sin arquero asignado.")

        update_data = {}
        for field in ("date", "time", "location"):
            value = getattr(payload, field, None)
            if value is not None:
                update_data[field] = value

        if not update_data:
            return match

        return await self.match_repo.update(match_id, **update_data)
    
    async def finalize_match(self, match_id: UUID, current_user) -> Match:
        role = self._get_user_role(current_user)
        if role != "player":
            raise PermissionError("Solo los jugadores pueden finalizar partidos.")
        user_id = getattr(current_user, "id", None)

        match = await self.match_repo.get_by_id(match_id)
        if not match:
            raise LookupError("Partido no encontrado.")
        if str(match.player_id) != str(user_id):
            raise PermissionError("Solo el creador del partido puede finalizarlo.")
        if match.status != "Asignado":
            raise ValueError("Solo se pueden finalizar partidos con arquero asignado.")
        return await self.match_repo.finalize(match_id)
    
    async def cancel_match(self, match_id: UUID, current_user) -> Match:        
        role = self._get_user_role(current_user)
        if role != "player":
            raise PermissionError("Solo los jugadores pueden cancelar partidos.")
        user_id = getattr(current_user, "id", None)
        
        match = await self.match_repo.get_by_id(match_id)
        if not match:
            raise LookupError("Partido no encontrado.")
        if str(match.player_id) != str(user_id):
            raise PermissionError("Solo el creador del partido puede cancelarlo.")
        if match.status != "Sin arquero":
            raise ValueError("Solo se pueden cancelar partidos que aún no tengan arquero asignado.")
        
        # Cancel the match
        cancelled_match = await self.match_repo.cancel(match_id)
        
        # Reject all pending offers for this match so no one can accept them later
        await self.offer_repo.reject_all_pending_for_match(match_id)
        print("hola")
        
        return cancelled_match