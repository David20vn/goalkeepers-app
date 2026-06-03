from app.repositories.player_repository import PlayerRepository


class PlayerService:
    def __init__(self, session):
        self.session = session
        self.player_repo = PlayerRepository(session)

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
        if role != "player":
            raise PermissionError("Solo los jugadores pueden crear un perfil de jugador.")

        user_id = getattr(current_user, "id", None)
        if user_id is None:
            raise ValueError("No se pudo identificar al usuario autenticado.")

        existing = await self.player_repo.get_by_user_id(user_id)
        if existing:
            raise ValueError("El usuario ya tiene un perfil de jugador creado.")

        data = {"user_id": user_id}
        return await self.player_repo.create(data)

    async def get_my_profile(self, current_user):
        role = self._get_user_role(current_user)
        if role != "player":
            raise PermissionError("Solo los jugadores tienen perfil de jugador.")

        user_id = getattr(current_user, "id", None)
        if user_id is None:
            raise ValueError("No se pudo identificar al usuario autenticado.")

        profile = await self.player_repo.get_by_user_id(user_id)
        if not profile:
            raise LookupError("Perfil de jugador no encontrado.")
        return profile

    async def get_profile_by_id(self, player_id):
        profile = await self.player_repo.get_by_id(player_id)
        if not profile:
            raise LookupError("Perfil de jugador no encontrado.")
        return profile

    async def update_profile(self, current_user, payload):
        role = self._get_user_role(current_user)
        if role != "player":
            raise PermissionError("Solo los jugadores pueden actualizar su perfil.")

        user_id = getattr(current_user, "id", None)
        if user_id is None:
            raise ValueError("No se pudo identificar al usuario autenticado.")

        profile = await self.player_repo.get_by_user_id(user_id)
        if not profile:
            raise LookupError("Perfil de jugador no encontrado.")

        update_fields = {}
        # future fields can be added here
        if not update_fields:
            return profile

        return await self.player_repo.update_profile(profile.id, **update_fields)

    async def list_profiles(self):
        return await self.player_repo.list_all()