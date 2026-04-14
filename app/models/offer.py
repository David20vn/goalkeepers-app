# app/models/offer.py

from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey
from sqlalchemy.sql import func

from app.core.database import Base


class Offer(Base):
    __tablename__ = "ofertas"

    id_oferta = Column(Integer, primary_key=True, index=True)
    id_partido = Column(Integer, ForeignKey("partidos.id_partido"), nullable=False)
    id_jugador = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    id_arquero = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    precio = Column(Numeric(10, 2), nullable=False)
    estado = Column(String(20), nullable=False, default="pendiente")

    created_by_user_id = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    created_by_role = Column(String(20), nullable=False)
    target_user_id = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)

    fecha_oferta = Column(DateTime, server_default=func.now(), nullable=False)