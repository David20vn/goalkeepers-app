# app/models/goalkeeper.py
from uuid import uuid4

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Goalkeeper(Base):
    __tablename__ = "goalkeepers"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    experience = Column(Text, nullable=True)
    availability = Column(Text, nullable=True)
    fixed_price = Column(Numeric(10, 2), nullable=False)
    average_rating = Column(Float, default=0.0, nullable=False)
    rating_count = Column(Integer, default=0, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relación con el modelo User (ajusta el back_populates según definas en User)
    user = relationship("User", back_populates="goalkeeper_profile")

    def __repr__(self):
        return f"<Goalkeeper(id={self.id}, user_id={self.user_id})>"