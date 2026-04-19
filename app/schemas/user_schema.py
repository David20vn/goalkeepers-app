from uuid import UUID
from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    role: str
    created_at: datetime

class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None