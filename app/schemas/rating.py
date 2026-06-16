from uuid import UUID
from pydantic import BaseModel, Field
from datetime import datetime

class RatingCreate(BaseModel):
    match_id: UUID
    score: int = Field(ge=1, le=5)

class RatingRead(BaseModel):
    id: UUID
    match_id: UUID
    player_id: UUID
    goalkeeper_id: UUID
    score: int
    created_at: datetime

    class Config:
        from_attributes = True