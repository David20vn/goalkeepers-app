from sqlalchemy import String, DateTime, func, Text, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from sqlalchemy.dialects.postgresql import UUID, ENUM
from datetime import datetime
import uuid


user_role_enum = ENUM("player", "goalkeeper", "admin", name="user_role", create_type=False)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(254), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    phone_number = Column(String(20), unique=True, nullable=True)
    role: Mapped[str] = mapped_column(user_role_enum, nullable=False, default="player")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    goalkeeper_profile = relationship("Goalkeeper", back_populates="user", uselist=False)
    player_profile = relationship("Player", back_populates="user", uselist=False)
