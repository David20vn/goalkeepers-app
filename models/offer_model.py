from sqlalchemy import Column, Integer, ForeignKey
from app.core.database import Base

class Offer(Base):
    __tablename__ = "ofertas"

    id_oferta = Column(Integer, primary_key=True)
    id_partido = Column(Integer, ForeignKey("partidos.id_partido"))