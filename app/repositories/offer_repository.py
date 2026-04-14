# app/repositories/offer_repository.py

from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.offer import Offer


class OfferRepository:
    """
    Capa de acceso a datos para ofertas.

    Esta clase no toma decisiones de negocio.
    Solo consulta, crea y actualiza registros en la base de datos.
    """

    @staticmethod
    def create(db: Session, offer_data: dict) -> Offer:
        """
        Crea una nueva oferta en la base de datos.
        No hace commit, porque eso lo controla el servicio.
        """
        offer = Offer(
            id_partido=offer_data["id_partido"],
            id_jugador=offer_data["id_jugador"],
            id_arquero=offer_data["id_arquero"],
            precio=offer_data["precio"],
            estado=offer_data.get("estado", "pendiente"),
            created_by_user_id=offer_data["created_by_user_id"],
            created_by_role=offer_data["created_by_role"],
            target_user_id=offer_data["target_user_id"],
        )

        db.add(offer)
        db.flush()      # asigna ID sin hacer commit
        db.refresh(offer)
        return offer

    @staticmethod
    def get_by_id(db: Session, offer_id: int) -> Optional[Offer]:
        """
        Obtiene una oferta por su ID.
        """
        return db.query(Offer).filter(Offer.id_oferta == offer_id).first()

    @staticmethod
    def get_by_id_for_update(db: Session, offer_id: int) -> Optional[Offer]:
        """
        Obtiene una oferta bloqueándola para evitar condiciones de carrera.
        Esto se usa dentro de una transacción.
        """
        return (
            db.query(Offer)
            .filter(Offer.id_oferta == offer_id)
            .with_for_update()
            .first()
        )

    @staticmethod
    def get_pending_offer_between(
        db: Session,
        id_partido: int,
        id_jugador: int,
        id_arquero: int,
    ) -> Optional[Offer]:
        """
        Busca si ya existe una oferta pendiente entre el mismo jugador,
        el mismo arquero y el mismo partido.
        """
        return (
            db.query(Offer)
            .filter(
                Offer.id_partido == id_partido,
                Offer.id_jugador == id_jugador,
                Offer.id_arquero == id_arquero,
                Offer.estado == "pendiente",
            )
            .first()
        )

    @staticmethod
    def list_sent_by_user(db: Session, user_id: int) -> List[Offer]:
        """
        Devuelve las ofertas enviadas por un usuario.
        """
        return (
            db.query(Offer)
            .filter(Offer.created_by_user_id == user_id)
            .order_by(Offer.fecha_oferta.desc())
            .all()
        )

    @staticmethod
    def list_received_by_user(db: Session, user_id: int) -> List[Offer]:
        """
        Devuelve las ofertas recibidas por un usuario.
        """
        return (
            db.query(Offer)
            .filter(Offer.target_user_id == user_id)
            .order_by(Offer.fecha_oferta.desc())
            .all()
        )

    @staticmethod
    def mark_accepted(db: Session, offer_id: int) -> Optional[Offer]:
        """
        Marca una oferta como aceptada.
        """
        offer = (
            db.query(Offer)
            .filter(Offer.id_oferta == offer_id)
            .with_for_update()
            .first()
        )

        if offer:
            offer.estado = "aceptada"
            db.flush()
            db.refresh(offer)

        return offer

    @staticmethod
    def mark_rejected(db: Session, offer_id: int) -> Optional[Offer]:
        """
        Marca una oferta como rechazada.
        """
        offer = (
            db.query(Offer)
            .filter(Offer.id_oferta == offer_id)
            .with_for_update()
            .first()
        )

        if offer:
            offer.estado = "rechazada"
            db.flush()
            db.refresh(offer)

        return offer

    @staticmethod
    def reject_other_offers_for_match(
        db: Session,
        id_partido: int,
        accepted_offer_id: int,
    ) -> int:
        """
        Rechaza automáticamente todas las demás ofertas del mismo partido,
        excepto la que fue aceptada.

        Devuelve la cantidad de filas afectadas.
        """
        updated_rows = (
            db.query(Offer)
            .filter(
                Offer.id_partido == id_partido,
                Offer.id_oferta != accepted_offer_id,
                Offer.estado == "pendiente",
            )
            .update(
                {"estado": "rechazada"},
                synchronize_session=False,
            )
        )

        db.flush()
        return updated_rows

    @staticmethod
    def list_by_match(db: Session, id_partido: int) -> List[Offer]:
        """
        Lista todas las ofertas de un partido.
        Útil para pantallas de detalle o auditoría.
        """
        return (
            db.query(Offer)
            .filter(Offer.id_partido == id_partido)
            .order_by(Offer.fecha_oferta.desc())
            .all()
        )