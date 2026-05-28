from uuid import UUID
from typing import Optional, List

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goalkeeper import Goalkeeper


class GoalkeeperRepository:


    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict) -> Goalkeeper:

        goalkeeper = Goalkeeper(**data)
        self.session.add(goalkeeper)
        await self.session.commit()
        await self.session.refresh(goalkeeper)
        return goalkeeper

    async def get_by_id(self, goalkeeper_id: UUID) -> Optional[Goalkeeper]:

        result = await self.session.execute(
            select(Goalkeeper).where(Goalkeeper.id == goalkeeper_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: UUID) -> Optional[Goalkeeper]:

        result = await self.session.execute(
            select(Goalkeeper).where(Goalkeeper.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def update_price(self, goalkeeper_id: UUID, new_price: float) -> Optional[Goalkeeper]:

        goalkeeper = await self.get_by_id(goalkeeper_id)
        if not goalkeeper:
            return None
        goalkeeper.fixed_price = new_price
        await self.session.commit()
        await self.session.refresh(goalkeeper)
        return goalkeeper

    async def update_profile(self, goalkeeper_id: UUID, **kwargs) -> Optional[Goalkeeper]:
        goalkeeper = await self.get_by_id(goalkeeper_id)
        if not goalkeeper:
            return None
        for field, value in kwargs.items():
            if hasattr(goalkeeper, field):
                setattr(goalkeeper, field, value)
        await self.session.commit()
        await self.session.refresh(goalkeeper)
        return goalkeeper

    async def update_average_rating(
        self, goalkeeper_id: UUID, new_rating: float
    ) -> Optional[Goalkeeper]:
        goalkeeper = await self.get_by_id(goalkeeper_id)
        if not goalkeeper:
            return None

        # Incremental average formula
        old_avg = goalkeeper.average_rating or 0.0
        old_count = goalkeeper.rating_count or 0
        new_count = old_count + 1
        new_avg = ((old_avg * old_count) + new_rating) / new_count

        goalkeeper.average_rating = new_avg
        goalkeeper.rating_count = new_count
        await self.session.commit()
        await self.session.refresh(goalkeeper)
        return goalkeeper

    async def list_by_min_rating(self, min_rating: float = 0.0) -> List[Goalkeeper]:
        result = await self.session.execute(
            select(Goalkeeper).where(Goalkeeper.average_rating >= min_rating)
        )
        return list(result.scalars().all())

    async def list_all(self) -> List[Goalkeeper]:
        result = await self.session.execute(select(Goalkeeper))
        return list(result.scalars().all())