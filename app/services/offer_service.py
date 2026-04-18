# app/services/offer_service.py

from typing import Any, List
from uuid import UUID

from app.core.database import SessionLocal
from app.models.enums import OfferStatus, OfferSender
from app.repositories.offer_repository import OfferRepository
from app.repositories.match_repository import MatchRepository
from app.repositories.goalkeeper_repository import GoalkeeperRepository
from app.repositories.user_repository import UserRepository


class OfferService:
    """
    Lógica de negocio del módulo de ofertas.

    Esta capa no debe ejecutar SQL directo.
    Solo coordina validaciones, reglas de negocio y llamadas al repositorio.
    """

    # -----------------------------
    # Helpers internos
    # -----------------------------
    @staticmethod
    def _get_attr(obj: Any, attr_name: str, default: Any = None) -> Any:
        if isinstance(obj, dict):
            return obj.get(attr_name, default)
        return getattr(obj, attr_name, default)

    @classmethod
    def _get_user_id(cls, current_user: Any) -> UUID:
        user_id = cls._get_attr(current_user, "id_usuario", None)
        if user_id is None:
            user_id = cls._get_attr(current_user, "id", None)

        if user_id is None:
            raise ValueError("No se pudo identificar el usuario autenticado.")

        return UUID(str(user_id))

    @classmethod
    def _get_user_role(cls, current_user: Any) -> str:
        role = cls._get_attr(current_user, "tipo_usuario", None)
        if role is None:
            role = cls._get_attr(current_user, "role", None)

        if role is None:
            raise ValueError("No se pudo determinar el rol del usuario autenticado.")

        return cls._normalize_sender_role(str(role))

    @staticmethod
    def _normalize_sender_role(value: str) -> str:
        """
        Normaliza roles en español o inglés y los convierte a los valores del enum.
        """
        role = value.lower().strip()

        if role in ("jugador", "player"):
            return OfferSender.player.value

        if role in ("arquero", "goalkeeper"):
            return OfferSender.goalkeeper.value

        raise ValueError("El rol debe ser 'jugador'/'player' o 'arquero'/'goalkeeper'.")

    @classmethod
    def _get_payload_match_id(cls, payload: Any) -> int:
        match_id = cls._get_attr(payload, "id_partido", None)
        if match_id is None:
            match_id = cls._get_attr(payload, "match_id", None)

        if match_id is None:
            raise ValueError("El campo 'id_partido' es obligatorio.")

        return int(match_id)

    @classmethod
    def _get_payload_target_user_id(cls, payload: Any) -> UUID:
        target_user_id = cls._get_attr(payload, "target_user_id", None)
        if target_user_id is None:
            target_user_id = cls._get_attr(payload, "id_usuario_destino", None)

        if target_user_id is None:
            raise ValueError("El campo 'target_user_id' es obligatorio.")

        return UUID(str(target_user_id))

    @classmethod
    def _get_match_status(cls, match: Any) -> str:
        status_value = cls._get_attr(match, "estado", None)
        if status_value is None:
            status_value = cls._get_attr(match, "status", None)

        if status_value is None:
            raise ValueError("No se pudo determinar el estado del partido.")

        return str(status_value).lower().strip()

    @classmethod
    def _get_match_player_id(cls, match: Any) -> UUID:
        player_id = cls._get_attr(match, "id_jugador", None)
        if player_id is None:
            player_id = cls._get_attr(match, "player_id", None)

        if player_id is None:
            raise ValueError("No se pudo determinar el jugador del partido.")

        return UUID(str(player_id))

    @classmethod
    def _get_offer_id(cls, offer: Any) -> UUID:
        offer_id = cls._get_attr(offer, "id_oferta", None)
        if offer_id is None:
            offer_id = cls._get_attr(offer, "id", None)

        if offer_id is None:
            raise ValueError("No se pudo determinar el ID de la oferta.")

        return UUID(str(offer_id))

    @classmethod
    def _get_offer_sender_role(cls, offer: Any) -> str:
        sender_role = cls._get_attr(offer, "sender_role", None)
        if sender_role is None:
            raise ValueError("La oferta no tiene rol de emisor.")

        return cls._normalize_sender_role(str(sender_role))

    @classmethod
    def _get_offer_recipient_id(cls, offer: Any) -> UUID:
        """
        Determina quién es el receptor de la oferta a partir de quién la envió.

        Si la oferta la envió el jugador, el receptor es el arquero.
        Si la oferta la envió el arquero, el receptor es el jugador.
        """
        sender_role = cls._get_offer_sender_role(offer)

        if sender_role == OfferSender.player.value:
            recipient_id = cls._get_attr(offer, "goalkeeper_id", None)
        else:
            recipient_id = cls._get_attr(offer, "player_id", None)

        if recipient_id is None:
            raise ValueError("No se pudo determinar el receptor de la oferta.")

        return UUID(str(recipient_id))

    # -----------------------------
    # Crear oferta
    # -----------------------------
    @classmethod
    def create_offer(cls, current_user: Any, payload: Any):
        """
        Crea una oferta nueva.

        Flujo:
        - Se identifica quién envía la oferta.
        - Se valida el partido.
        - Se valida el receptor.
        - Se calcula el precio fijo según el arquero.
        - Se crea la oferta en estado pendiente.
        """
        sender_user_id = cls._get_user_id(current_user)
        sender_role = cls._get_user_role(current_user)

        match_id = cls._get_payload_match_id(payload)
        target_user_id = cls._get_payload_target_user_id(payload)

        if sender_user_id == target_user_id:
            raise ValueError("No puedes enviarte una oferta a ti mismo.")

        with SessionLocal() as db:
            try:
                with db.begin():
                    match = MatchRepository.get_by_id_for_update(db, match_id)
                    if not match:
                        raise LookupError("El partido no existe.")

                    match_status = cls._get_match_status(match)
                    if match_status != "sin_arquero":
                        raise ValueError("No se pueden crear ofertas sobre un partido ya asignado.")

                    target_user = UserRepository.get_by_id(db, target_user_id)
                    if not target_user:
                        raise LookupError("El usuario destino no existe.")

                    target_role = cls._normalize_sender_role(
                        str(
                            cls._get_attr(
                                target_user,
                                "tipo_usuario",
                                cls._get_attr(target_user, "role", "")
                            )
                        )
                    )

                    # Regla: jugador/player -> arquero/goalkeeper
                    # Regla: arquero/goalkeeper -> jugador/player
                    if sender_role == OfferSender.player.value:
                        if target_role != OfferSender.goalkeeper.value:
                            raise ValueError("Un jugador solo puede enviar ofertas a un arquero.")

                        match_player_id = cls._get_match_player_id(match)
                        if match_player_id != sender_user_id:
                            raise PermissionError("Solo puedes ofertar sobre partidos que te pertenecen.")

                        goalkeeper_profile = GoalkeeperRepository.get_profile_by_user_id(db, target_user_id)
                        if not goalkeeper_profile:
                            raise LookupError("El arquero no tiene un perfil público activo.")

                        price = float(goalkeeper_profile.precio)
                        player_id = sender_user_id
                        goalkeeper_id = target_user_id

                    elif sender_role == OfferSender.goalkeeper.value:
                        if target_role != OfferSender.player.value:
                            raise ValueError("Un arquero solo puede enviar ofertas a un jugador.")

                        goalkeeper_profile = GoalkeeperRepository.get_profile_by_user_id(db, sender_user_id)
                        if not goalkeeper_profile:
                            raise LookupError("No tienes un perfil de arquero activo.")

                        price = float(goalkeeper_profile.precio)
                        player_id = target_user_id
                        goalkeeper_id = sender_user_id

                    else:
                        raise PermissionError("Rol no autorizado para crear ofertas.")

                    existing_offer = OfferRepository.get_pending_offer_between(
                        db=db,
                        match_id=match_id,
                        player_id=player_id,
                        goalkeeper_id=goalkeeper_id,
                        sender_role=sender_role,
                    )
                    if existing_offer:
                        raise ValueError("Ya existe una oferta pendiente entre estos usuarios para este partido.")

                    offer_data = {
                        "match_id": match_id,
                        "sender_role": sender_role,
                        "player_id": player_id,
                        "goalkeeper_id": goalkeeper_id,
                        "price": price,
                        "status": OfferStatus.pending.value,
                    }

                    offer = OfferRepository.create(db, offer_data)
                    db.flush()
                    return offer

            except Exception:
                db.rollback()
                raise

    # -----------------------------
    # Listar ofertas enviadas
    # -----------------------------
    @classmethod
    def list_sent_offers(cls, current_user: Any) -> List[Any]:
        user_id = cls._get_user_id(current_user)

        with SessionLocal() as db:
            return OfferRepository.list_sent_by_user(db, user_id)

    # -----------------------------
    # Listar ofertas recibidas
    # -----------------------------
    @classmethod
    def list_received_offers(cls, current_user: Any) -> List[Any]:
        user_id = cls._get_user_id(current_user)

        with SessionLocal() as db:
            return OfferRepository.list_received_by_user(db, user_id)

    # -----------------------------
    # Obtener una oferta por ID
    # -----------------------------
    @classmethod
    def get_offer_by_id(cls, current_user: Any, offer_id: Any):
        user_id = cls._get_user_id(current_user)

        with SessionLocal() as db:
            offer = OfferRepository.get_by_id(db, UUID(str(offer_id)))
            if not offer:
                raise LookupError("La oferta no existe.")

            # Solo pueden verla quienes participan en ella.
            if user_id not in (
                UUID(str(cls._get_attr(offer, "player_id"))),
                UUID(str(cls._get_attr(offer, "goalkeeper_id"))),
            ):
                raise PermissionError("No tienes permiso para ver esta oferta.")

            return offer

    # -----------------------------
    # Aceptar oferta
    # -----------------------------
    @classmethod
    def accept_offer(cls, current_user: Any, offer_id: Any):
        """
        Acepta una oferta y asigna el arquero al partido en una sola transacción.

        Reglas:
        - Solo el receptor puede aceptar.
        - El partido debe seguir sin arquero.
        - La oferta debe estar pendiente.
        - Se bloquea el partido para evitar doble asignación.
        """
        user_id = cls._get_user_id(current_user)

        with SessionLocal() as db:
            try:
                with db.begin():
                    offer = OfferRepository.get_by_id_for_update(db, UUID(str(offer_id)))
                    if not offer:
                        raise LookupError("La oferta no existe.")

                    offer_status = str(cls._get_attr(offer, "status", "")).lower().strip()
                    if offer_status != OfferStatus.pending.value:
                        raise ValueError("Solo se pueden aceptar ofertas pendientes.")

                    recipient_id = cls._get_offer_recipient_id(offer)
                    if recipient_id != user_id:
                        raise PermissionError("Solo el receptor de la oferta puede aceptarla.")

                    match_id = int(cls._get_attr(offer, "match_id"))
                    match = MatchRepository.get_by_id_for_update(db, match_id)
                    if not match:
                        raise LookupError("El partido asociado a la oferta no existe.")

                    match_status = cls._get_match_status(match)
                    if match_status != "sin_arquero":
                        raise ValueError("Este partido ya tiene un arquero asignado.")

                    goalkeeper_id = UUID(str(cls._get_attr(offer, "goalkeeper_id")))

                    # Asignación del arquero al partido
                    MatchRepository.assign_goalkeeper(
                        db=db,
                        id_partido=match_id,
                        id_arquero_asignado=goalkeeper_id,
                    )

                    # Marcar la oferta aceptada
                    OfferRepository.mark_accepted(db, UUID(str(cls._get_offer_id(offer))))

                    # Rechazar las demás ofertas del mismo partido
                    OfferRepository.reject_other_offers_for_match(
                        db=db,
                        match_id=match_id,
                        accepted_offer_id=UUID(str(cls._get_offer_id(offer))),
                    )

                    db.flush()

                    return {
                        "message": "Oferta aceptada y arquero asignado correctamente.",
                        "offer_id": str(cls._get_offer_id(offer)),
                        "match_id": match_id,
                        "status": OfferStatus.accepted.value,
                    }

            except Exception:
                db.rollback()
                raise

    # -----------------------------
    # Rechazar oferta
    # -----------------------------
    @classmethod
    def reject_offer(cls, current_user: Any, offer_id: Any):
        """
        Rechaza una oferta.

        Solo el receptor puede rechazarla.
        """
        user_id = cls._get_user_id(current_user)

        with SessionLocal() as db:
            try:
                with db.begin():
                    offer = OfferRepository.get_by_id_for_update(db, UUID(str(offer_id)))
                    if not offer:
                        raise LookupError("La oferta no existe.")

                    recipient_id = cls._get_offer_recipient_id(offer)
                    if recipient_id != user_id:
                        raise PermissionError("Solo el receptor de la oferta puede rechazarla.")

                    offer_status = str(cls._get_attr(offer, "status", "")).lower().strip()
                    if offer_status != OfferStatus.pending.value:
                        raise ValueError("Solo se pueden rechazar ofertas pendientes.")

                    OfferRepository.mark_rejected(db, UUID(str(cls._get_offer_id(offer))))
                    db.flush()

                    return {
                        "message": "Oferta rechazada correctamente.",
                        "offer_id": str(cls._get_offer_id(offer)),
                        "status": OfferStatus.rejected.value,
                    }

            except Exception:
                db.rollback()
                raise