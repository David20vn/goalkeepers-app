# app/schemas/goalkeeper.py
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class GoalkeeperCreate(BaseModel):
    fixed_price: float
    experience: str | None = None
    availability: str | None = None

class GoalkeeperUpdate(BaseModel):
    fixed_price: float | None = None
    experience: str | None = None
    availability: str | None = None

class GoalkeeperRead(BaseModel):
    id: UUID
    user_id: UUID
    experience: str | None
    availability: str | None
    fixed_price: float
    average_rating: float
    rating_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True