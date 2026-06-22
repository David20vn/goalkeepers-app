from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

class VenueCreate(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float

class VenueRead(BaseModel):
    id: UUID
    name: str
    address: str
    latitude: float
    longitude: float
    created_at: datetime

    class Config:
        from_attributes = True