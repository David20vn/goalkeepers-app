from uuid import UUID
from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.offer import Offer

class OfferRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict) -> Offer:
        offer = Offer(**data)
        self.session.add(offer)
        await self.session.commit()
        await self.session.refresh(offer)
        return offer

    async def get_by_id(self, offer_id: UUID) -> Optional[Offer]:
        result = await self.session.execute(
            select(Offer).where(Offer.id == offer_id)
        )
        return result.scalar_one_or_none()

    async def list_sent_by_user(self, user_id: UUID, role: str) -> List[Offer]:
        if role == "player":
            result = await self.session.execute(
                select(Offer).where(
                    Offer.player_id == user_id,
                    Offer.sender_role == "player"
                )
            )
        else:  # goalkeeper
            result = await self.session.execute(
                select(Offer).where(
                    Offer.goalkeeper_id == user_id,
                    Offer.sender_role == "goalkeeper"
                )
            )
        return list(result.scalars().all())

    async def list_received_by_user(self, user_id: UUID, role: str) -> List[Offer]:
        if role == "player":
            result = await self.session.execute(
                select(Offer).where(
                    Offer.player_id == user_id,
                    Offer.sender_role == "goalkeeper"
                )
            )
        else:  # goalkeeper
            result = await self.session.execute(
                select(Offer).where(
                    Offer.goalkeeper_id == user_id,
                    Offer.sender_role == "player"
                )
            )
        return list(result.scalars().all())

    async def update_status(self, offer_id: UUID, status: str) -> Optional[Offer]:
        offer = await self.get_by_id(offer_id)
        if not offer:
            return None
        offer.status = status
        await self.session.commit()
        await self.session.refresh(offer)
        return offer

    async def reject_pending_offers_for_match_except(
        self, match_id: UUID, except_offer_id: UUID
    ) -> None:
        await self.session.execute(
            update(Offer)
            .where(
                Offer.match_id == match_id,
                Offer.status == "pending",
                Offer.id != except_offer_id
            )
            .values(status="rejected")
        )
        await self.session.commit()

    async def exists_pending_offer(
        self, match_id: UUID, player_id: UUID, goalkeeper_id: UUID
    ) -> bool:
        result = await self.session.execute(
            select(Offer).where(
                Offer.match_id == match_id,
                Offer.player_id == player_id,
                Offer.goalkeeper_id == goalkeeper_id,
                Offer.status == "pending"
            )
        )
        return result.scalar_one_or_none() is not None
    
    async def reject_all_pending_for_match(self, match_id: UUID) -> None:
        await self.session.execute(
            update(Offer)
            .where(
                Offer.match_id == match_id,
                Offer.status == "pending"
            )
            .values(status="rejected")
        )
        await self.session.commit()