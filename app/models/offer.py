# app/models/offer.py

from uuid import uuid4

from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, func, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum

from app.core.database import Base


class Offer(Base):
    __tablename__ = "offers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)

    match_id = Column(Integer, ForeignKey("matches.id_partido", ondelete="CASCADE"), nullable=False)
    player_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    goalkeeper_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    status = Column(
    Enum(OfferStatus, name="offer_status"),
    nullable=False,
    default=Offer_status.PENDING
    )

    sender_role = Column(
    Enum(OfferSender, name="offer_sender"),
    nullable=False
    )

    price = Column(Numeric(10, 2), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relaciones opcionales pero muy útiles
    match = relationship("Match", back_populates="offers")
    player = relationship("User", foreign_keys=[player_id])
    goalkeeper = relationship("User", foreign_keys=[goalkeeper_id])