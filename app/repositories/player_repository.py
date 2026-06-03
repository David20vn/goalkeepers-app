from uuid import UUID
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.player import Player


class PlayerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict) -> Player:
        player = Player(**data)
        self.session.add(player)
        await self.session.commit()
        await self.session.refresh(player)
        return player

    async def get_by_id(self, player_id: UUID) -> Optional[Player]:
        result = await self.session.execute(
            select(Player).where(Player.id == player_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: UUID) -> Optional[Player]:
        result = await self.session.execute(
            select(Player).where(Player.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_profile(self, player_id: UUID, **kwargs) -> Optional[Player]:
        player = await self.get_by_id(player_id)
        if not player:
            return None
        for field, value in kwargs.items():
            if hasattr(player, field):
                setattr(player, field, value)
        await self.session.commit()
        await self.session.refresh(player)
        return player

    async def list_all(self) -> List[Player]:
        result = await self.session.execute(select(Player))
        return list(result.scalars().all())