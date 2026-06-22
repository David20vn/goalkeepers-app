# app/schemas/user_schema.py

from uuid import UUID
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    PLAYER = "player"
    GOALKEEPER = "goalkeeper"
    ADMIN = "admin"


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    phone_number: str | None = None
    role: UserRole
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone_number: str | None = None