from typing import Optional

from app.repositories.goalkeeper_repository import GoalkeeperRepository
from app.repositories.user_repository import UserRepository


class GoalkeeperService:
    def __init__(self, session):
        self.session = session
        self.goalkeeper_repo = GoalkeeperRepository(session)
        self.user_repo = UserRepository(session)

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

    async def create_profile(self, current_user, payload):
        role = self._get_user_role(current_user)
        if role != "goalkeeper":
            raise PermissionError("Solo los arqueros pueden crear un perfil.")

        user_id = getattr(current_user, "id", None)
        if user_id is None:
            raise ValueError("No se pudo identificar al usuario autenticado.")

        existing = await self.goalkeeper_repo.get_by_user_id(user_id)
        if existing:
            raise ValueError("El usuario ya tiene un perfil de arquero creado.")

        fixed_price = self._get_attr(payload, "fixed_price", "price")
        if fixed_price is None:
            raise ValueError("El precio fijo es obligatorio.")

        data = {
            "user_id": user_id,
            "fixed_price": fixed_price,
            "experience": self._get_attr(payload, "experience"),
            "availability": self._get_attr(payload, "availability"),
        }

        return await self.goalkeeper_repo.create(data)

    async def get_my_profile(self, current_user):
        role = self._get_user_role(current_user)
        if role != "goalkeeper":
            raise PermissionError("Solo los arqueros tienen perfil.")

        user_id = getattr(current_user, "id", None)
        if user_id is None:
            raise ValueError("No se pudo identificar al usuario autenticado.")

        profile = await self.goalkeeper_repo.get_by_user_id(user_id)
        if not profile:
            raise LookupError("Perfil de arquero no encontrado.")
        return profile

    async def get_profile_by_id(self, goalkeeper_id):
        profile = await self.goalkeeper_repo.get_by_id(goalkeeper_id)
        if not profile:
            raise LookupError("Perfil de arquero no encontrado.")
        return profile

    async def update_profile(self, current_user, payload):
        role = self._get_user_role(current_user)
        if role != "goalkeeper":
            raise PermissionError("Solo los arqueros pueden actualizar su perfil.")

        user_id = getattr(current_user, "id", None)
        if user_id is None:
            raise ValueError("No se pudo identificar al usuario autenticado.")

        profile = await self.goalkeeper_repo.get_by_user_id(user_id)
        if not profile:
            raise LookupError("Perfil de arquero no encontrado.")

        update_fields = {}
        for field in ("experience", "availability", "fixed_price"):
            value = self._get_attr(payload, field)
            if value is not None:
                update_fields[field] = value

        if not update_fields:
            raise ValueError("No se proporcionaron campos para actualizar.")

        return await self.goalkeeper_repo.update_profile(profile.id, **update_fields)

    async def update_rating(self, goalkeeper_id: int, new_rating: float):
        return await self.goalkeeper_repo.update_average_rating(goalkeeper_id, new_rating)

    async def list_profiles(
        self,
        min_rating: Optional[float] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ):
        return await self.goalkeeper_repo.list_filtered(
            min_rating=min_rating,
            min_price=min_price,
            max_price=max_price,
        )