# app/schemas/auth_schema.py

from pydantic import BaseModel, EmailStr, validator
from app.schemas.user_schema import UserRole
import uuid
import re


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone_number: str | None = None
    role: UserRole = UserRole.PLAYER

    @validator("phone_number")
    def validate_phone(cls, v):
        if v is not None and not re.match(r'^\+?[1-9]\d{1,14}$', v):
            raise ValueError("Número de teléfono inválido. Usa formato internacional, ej. +573001234567")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    role: UserRole
    phone_number: str | None = None  # práctico para el frontend


class TokenPayload(BaseModel):
    id: uuid.UUID
    role: UserRole
    phone_number: str | None = None  # opcional en el JWT