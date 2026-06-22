from uuid import UUID
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.venue import Venue

class VenueRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict) -> Venue:
        venue = Venue(**data)
        self.session.add(venue)
        await self.session.commit()
        await self.session.refresh(venue)
        return venue

    async def get_by_id(self, venue_id: UUID) -> Optional[Venue]:
        result = await self.session.execute(
            select(Venue).where(Venue.id == venue_id)
        )
        return result.scalar_one_or_none()

    async def list_all(self) -> List[Venue]:
        result = await self.session.execute(select(Venue))
        return list(result.scalars().all())