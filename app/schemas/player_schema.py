# app/schemas/player.py
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class PlayerCreate(BaseModel):
    # No extra fields required; profile is just linked to user
    pass

class PlayerUpdate(BaseModel):
    # Add fields here later (e.g., preferred_position)
    pass

class PlayerRead(BaseModel):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True