from uuid import UUID
from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.match import Match


class MatchRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict) -> Match:
        match = Match(**data)
        self.session.add(match)
        await self.session.commit()
        await self.session.refresh(match)
        return match

    async def get_by_id(self, match_id: UUID) -> Optional[Match]:
        result = await self.session.execute(
            select(Match).where(Match.id == match_id)
        )
        return result.scalar_one_or_none()

    async def list_by_player(self, player_id: UUID) -> List[Match]:
        result = await self.session.execute(
            select(Match).where(Match.player_id == player_id)
        )
        return list(result.scalars().all())

    async def list_available(self) -> List[Match]:
        result = await self.session.execute(
            select(Match).where(Match.status == "Sin arquero")
        )
        return list(result.scalars().all())

    async def update(self, match_id: UUID, **kwargs) -> Optional[Match]:
        match = await self.get_by_id(match_id)
        if not match:
            return None
        for field, value in kwargs.items():
            if hasattr(match, field):
                setattr(match, field, value)
        await self.session.commit()
        await self.session.refresh(match)
        return match

    async def assign_goalkeeper(self, match_id: UUID, goalkeeper_id: UUID, status: str = "Asignado") -> Optional[Match]:
        match = await self.get_by_id(match_id)
        if not match:
            return None
        match.goalkeeper_id = goalkeeper_id
        match.status = status
        await self.session.commit()
        await self.session.refresh(match)
        return match

    async def finalize(self, match_id: UUID) -> Optional[Match]:
        match = await self.get_by_id(match_id)
        if not match:
            return None
        match.status = "Finalizado"
        await self.session.commit()
        await self.session.refresh(match)
        return match