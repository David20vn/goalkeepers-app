from uuid import UUID
from app.repositories.rating_repository import RatingRepository
from app.repositories.match_repository import MatchRepository
from app.repositories.goalkeeper_repository import GoalkeeperRepository

class RatingService:
    def __init__(self, session):
        self.session = session
        self.rating_repo = RatingRepository(session)
        self.match_repo = MatchRepository(session)
        self.goalkeeper_repo = GoalkeeperRepository(session)

    @staticmethod
    def _get_user_role(current_user):
        role = getattr(current_user, "role", None) or getattr(current_user, "user_role", None)
        if not role:
            raise ValueError("El usuario autenticado no tiene un rol válido.")
        return role

    async def rate_goalkeeper(self, current_user, payload):
        role = self._get_user_role(current_user)
        if role != "player":
            raise PermissionError("Solo los jugadores pueden calificar arqueros.")

        user_id = getattr(current_user, "id", None)
        match_id = payload.match_id

        match = await self.match_repo.get_by_id(match_id)
        if not match:
            raise LookupError("Partido no encontrado.")
        if str(match.player_id) != str(user_id):
            raise PermissionError("Solo el jugador del partido puede calificar.")
        if match.status != "Finalizado":
            raise ValueError("El partido aún no ha finalizado.")
        if not match.goalkeeper_id:
            raise ValueError("El partido no tiene arquero asignado.")

        # Check uniqueness
        existing = await self.rating_repo.get_by_match(match_id)
        if existing:
            raise ValueError("Ya existe una calificación para este partido.")

        rating_data = {
            "match_id": match_id,
            "player_id": user_id,
            "goalkeeper_id": match.goalkeeper_id,
            "score": payload.score,
        }
        rating = await self.rating_repo.create(rating_data)

        # 1. Find goalkeeper profile by user_id (match.goalkeeper_id is a user ID)
        gk_profile = await self.goalkeeper_repo.get_by_user_id(match.goalkeeper_id)
        if not gk_profile:
            raise ValueError("El arquero no tiene perfil.")

        # 2. Update using the profile's primary key
        await self.goalkeeper_repo.update_average_rating(
            gk_profile.id, payload.score
        )

        return rating

    async def get_goalkeeper_ratings(self, goalkeeper_id: UUID):
        return await self.rating_repo.list_by_goalkeeper(goalkeeper_id)

    async def get_goalkeeper_average(self, goalkeeper_id: UUID) -> float:
        # Retrieve from goalkeeper profile (faster)
        gk = await self.goalkeeper_repo.get_by_id(goalkeeper_id)
        if not gk:
            raise LookupError("Arquero no encontrado.")
        return gk.average_rating