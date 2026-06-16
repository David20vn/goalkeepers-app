from uuid import UUID
from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.rating import Rating

class RatingRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict) -> Rating:
        rating = Rating(**data)
        self.session.add(rating)
        await self.session.commit()
        await self.session.refresh(rating)
        return rating

    async def get_by_id(self, rating_id: UUID) -> Optional[Rating]:
        result = await self.session.execute(
            select(Rating).where(Rating.id == rating_id)
        )
        return result.scalar_one_or_none()

    async def get_by_match(self, match_id: UUID) -> Optional[Rating]:
        result = await self.session.execute(
            select(Rating).where(Rating.match_id == match_id)
        )
        return result.scalar_one_or_none()

    async def list_by_goalkeeper(self, goalkeeper_id: UUID) -> List[Rating]:
        result = await self.session.execute(
            select(Rating).where(Rating.goalkeeper_id == goalkeeper_id)
        )
        return list(result.scalars().all())

    async def get_average_score(self, goalkeeper_id: UUID) -> float:
        result = await self.session.execute(
            select(func.avg(Rating.score)).where(Rating.goalkeeper_id == goalkeeper_id)
        )
        avg = result.scalar()
        return float(avg) if avg else 0.0