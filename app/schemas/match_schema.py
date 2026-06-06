from datetime import date, time, datetime
from uuid import UUID
from pydantic import BaseModel
from typing import Optional


class MatchCreate(BaseModel):
    date: date
    time: time
    location: str


class MatchUpdate(BaseModel):
    date: Optional[date] = None
    time: Optional[time] = None
    location: Optional[str] = None


class MatchRead(BaseModel):
    id: UUID
    player_id: UUID
    goalkeeper_id: UUID | None
    date: date
    time: time
    location: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True