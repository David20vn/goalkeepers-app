# app/schemas/offer_schema.py

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class OfferStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class OfferSender(str, Enum):
    PLAYER = "player"
    GOALKEEPER = "goalkeeper"


class OfferBase(BaseModel):
    match_id: int = Field(..., description="ID del partido al que pertenece la oferta")
    player_id: UUID = Field(..., description="ID del jugador asociado a la oferta")
    goalkeeper_id: UUID = Field(..., description="ID del arquero asociado a la oferta")
    sender_role: OfferSender = Field(..., description="Rol del usuario que envía la oferta")
    price: Decimal = Field(..., decimal_places=2, max_digits=10, description="Precio fijo de la oferta")


class OfferCreate(BaseModel):
    """
    Esquema de entrada para crear una oferta.

    El service puede completar player_id / goalkeeper_id / price / sender_role
    según el usuario autenticado y las reglas de negocio.
    """
    match_id: int = Field(..., description="ID del partido")

    # Opcionales para permitir que el service decida cómo construir la oferta
    player_id: UUID | None = Field(default=None, description="ID del jugador receptor o creador")
    goalkeeper_id: UUID | None = Field(default=None, description="ID del arquero receptor o creador")
    sender_role: OfferSender | None = Field(default=None, description="Rol del remitente")


class OfferRead(BaseModel):
    id: UUID
    match_id: int
    player_id: UUID
    goalkeeper_id: UUID
    status: OfferStatus
    sender_role: OfferSender
    price: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OfferActionResponse(BaseModel):
    success: bool = True
    message: str
    offer_id: UUID
    status: OfferStatus

    model_config = ConfigDict(from_attributes=True)