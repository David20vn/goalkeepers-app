# app/repositories/offer_repository.py

from typing import Any, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.offer import Offer


class OfferRepository:
    """
    Capa de acceso a datos para la tabla offers.

    Esta clase:
    - no decide reglas de negocio
    - no valida permisos
    - no toma decisiones de flujo

    Solo crea, consulta y actualiza registros.
    """

    @staticmethod
    def create(db: Session, offer_data: dict) -> Offer:
        """
        Crea una nueva oferta.

        Espera un diccionario con claves como:
        - match_id
        - sender_role
        - player_id
        - goalkeeper_id
        - price
        - status

        No hace commit. Eso lo controla el service.
        """
        offer = Offer(
            match_id=offer_data["match_id"],
            sender_role=offer_data["sender_role"],
            player_id=offer_data["player_id"],
            goalkeeper_id=offer_data["goalkeeper_id"],
            price=offer_data["price"],
            status=offer_data.get("status", "pending"),
        )

        db.add(offer)
        db.flush()
        db.refresh(offer)
        return offer

    @staticmethod
    def get_by_id(db: Session, offer_id: UUID) -> Optional[Offer]:
        """
        Devuelve una oferta por su UUID.
        """
        return db.query(Offer).filter(Offer.id == offer_id).first()

    @staticmethod
    def get_by_id_for_update(db: Session, offer_id: UUID) -> Optional[Offer]:
        """
        Devuelve una oferta bloqueándola dentro de la transacción.

        Útil para evitar condiciones de carrera al aceptar o rechazar ofertas.
        """
        return (
            db.query(Offer)
            .filter(Offer.id == offer_id)
            .with_for_update()
            .first()
        )

    @staticmethod
    def get_pending_offer_between(
        db: Session,
        match_id: int,
        player_id: UUID,
        goalkeeper_id: UUID,
        sender_role: str,
    ) -> Optional[Offer]:
        """
        Busca si ya existe una oferta pendiente entre:
        - el mismo partido
        - el mismo jugador
        - el mismo arquero
        - el mismo rol de envío

        Esto sirve para evitar ofertas duplicadas exactas.
        """
        return (
            db.query(Offer)
            .filter(
                Offer.match_id == match_id,
                Offer.player_id == player_id,
                Offer.goalkeeper_id == goalkeeper_id,
                Offer.sender_role == sender_role,
                Offer.status == "pending",
            )
            .first()
        )

    @staticmethod
    def list_sent_by_user(db: Session, user_id: UUID) -> List[Offer]:
        """
        Devuelve SOLO las ofertas que el usuario ha enviado.

        Se determina según:
        - Si es player → player_id == user_id AND sender_role = 'player'
        - Si es goalkeeper → goalkeeper_id == user_id AND sender_role = 'goalkeeper'
        """
        return (
            db.query(Offer)
            .filter(
                (
                    (Offer.player_id == user_id) &
                    (Offer.sender_role == OfferSender.player)
                ) |
                (
                    (Offer.goalkeeper_id == user_id) &
                    (Offer.sender_role == OfferSender.goalkeeper)
                )
            )
            .order_by(Offer.created_at.desc())
            .all()
        )

    @staticmethod
    def list_received_by_user(db: Session, user_id: UUID) -> List[Offer]:
        """
        Devuelve SOLO las ofertas que el usuario ha recibido.

        Se determina según:
        - Si es player → player_id == user_id AND sender_role = 'goalkeeper'
        - Si es goalkeeper → goalkeeper_id == user_id AND sender_role = 'player'
        """
        return (
            db.query(Offer)
            .filter(
                (
                    (Offer.player_id == user_id) &
                    (Offer.sender_role == OfferSender.goalkeeper)
                ) |
                (
                    (Offer.goalkeeper_id == user_id) &
                    (Offer.sender_role == OfferSender.player)
                )
            )
            .order_by(Offer.created_at.desc())
            .all()
        )

    @staticmethod
    def list_by_match(db: Session, match_id: int) -> List[Offer]:
        """
        Devuelve todas las ofertas asociadas a un partido.
        """
        return (
            db.query(Offer)
            .filter(Offer.match_id == match_id)
            .order_by(Offer.created_at.desc())
            .all()
        )

    @staticmethod
    def mark_accepted(db: Session, offer_id: UUID) -> Optional[Offer]:
        """
        Marca una oferta como aceptada.
        """
        offer = (
            db.query(Offer)
            .filter(Offer.id == offer_id)
            .with_for_update()
            .first()
        )

        if offer:
            offer.status = "accepted"
            db.flush()
            db.refresh(offer)

        return offer

    @staticmethod
    def mark_rejected(db: Session, offer_id: UUID) -> Optional[Offer]:
        """
        Marca una oferta como rechazada.
        """
        offer = (
            db.query(Offer)
            .filter(Offer.id == offer_id)
            .with_for_update()
            .first()
        )

        if offer:
            offer.status = "rejected"
            db.flush()
            db.refresh(offer)

        return offer

    @staticmethod
    def reject_other_offers_for_match(
        db: Session,
        match_id: int,
        accepted_offer_id: UUID,
    ) -> int:
        """
        Rechaza automáticamente todas las demás ofertas del mismo partido,
        excepto la que fue aceptada.

        Devuelve la cantidad de filas afectadas.
        """
        updated_rows = (
            db.query(Offer)
            .filter(
                Offer.match_id == match_id,
                Offer.id != accepted_offer_id,
                Offer.status == "pending",
            )
            .update(
                {"status": "rejected"},
                synchronize_session=False,
            )
        )

        db.flush()
        return updated_rows

    @staticmethod
    def has_pending_offer_from_sender(
        db: Session,
        match_id: int,
        player_id: UUID,
        goalkeeper_id: UUID,
        sender_role: str,
    ) -> bool:
        """
        Verifica si ya existe una oferta pendiente exactamente igual.

        Útil para evitar duplicados antes de insertar una nueva oferta.
        """
        exists_offer = (
            db.query(Offer)
            .filter(
                Offer.match_id == match_id,
                Offer.player_id == player_id,
                Offer.goalkeeper_id == goalkeeper_id,
                Offer.sender_role == sender_role,
                Offer.status == "pending",
            )
            .first()
        )
        return exists_offer is not None