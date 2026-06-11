from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class OfferCreate(BaseModel):
    match_id: UUID
    player_id: UUID | None = None
    goalkeeper_id: UUID | None = None


class OfferRead(BaseModel):
    id: UUID
    match_id: UUID
    player_id: UUID
    goalkeeper_id: UUID
    sender_role: str
    price: float
    status: str
    created_at: datetime
    updated_at: datetime

class OfferActionResponse(BaseModel):
    id: UUID
    status: str
    message: str