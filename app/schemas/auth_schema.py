from pydantic import BaseModel, EmailStr
from app.schemas.user_schema import UserRole
import uuid


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.PLAYER


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    role: UserRole


class TokenPayload(BaseModel):
    id: uuid.UUID
    role: UserRole
