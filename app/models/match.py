# app/models/match.py
from sqlalchemy import Column, String, Date, Time, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from uuid import uuid4
from app.core.database import Base

class Match(Base):
    __tablename__ = "matches"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    player_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    goalkeeper_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    date = Column(Date, nullable=False)
    time = Column(Time, nullable=False)
    location = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False, default="Sin arquero")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "status IN ('Sin arquero', 'Asignado', 'Finalizado')",
            name="ck_match_status"
        ),
    )

    player = relationship("User", foreign_keys=[player_id], backref="matches_created")
    goalkeeper = relationship("User", foreign_keys=[goalkeeper_id], backref="matches_assigned")
