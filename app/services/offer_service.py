# app/services/offer_service.py

from typing import Any, List

from app.core.database import SessionLocal
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
    def _get_user_id(cls, current_user: Any) -> int:
        user_id = cls._get_attr(current_user, "id_usuario", None)
        if user_id is None:
            user_id = cls._get_attr(current_user, "id", None)

        if user_id is None:
            raise ValueError("No se pudo identificar el usuario autenticado.")

        return int(user_id)

    @classmethod
    def _get_user_role(cls, current_user: Any) -> str:
        role = cls._get_attr(current_user, "tipo_usuario", None)
        if role is None:
            role = cls._get_attr(current_user, "role", None)

        if role is None:
            raise ValueError("No se pudo determinar el rol del usuario autenticado.")

        return str(role)

    @staticmethod
    def _validate_role(value: str) -> str:
        role = value.lower().strip()
        if role not in ("jugador", "arquero"):
            raise ValueError("El rol debe ser 'jugador' o 'arquero'.")
        return role

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
        sender_role = cls._validate_role(cls._get_user_role(current_user))

        match_id = cls._get_attr(payload, "id_partido", None)
        target_user_id = cls._get_attr(payload, "target_user_id", None)

        if match_id is None:
            raise ValueError("El campo 'id_partido' es obligatorio.")

        if target_user_id is None:
            raise ValueError("El campo 'target_user_id' es obligatorio.")

        target_user_id = int(target_user_id)
        match_id = int(match_id)

        with SessionLocal() as db:
            try:
                with db.begin():
                    match = MatchRepository.get_by_id_for_update(db, match_id)
                    if not match:
                        raise LookupError("El partido no existe.")

                    if match.estado != "sin_arquero":
                        raise ValueError("No se pueden crear ofertas sobre un partido ya asignado.")

                    target_user = UserRepository.get_by_id(db, target_user_id)
                    if not target_user:
                        raise LookupError("El usuario destino no existe.")

                    target_role = cls._validate_role(cls._get_attr(target_user, "tipo_usuario", ""))

                    if sender_user_id == target_user_id:
                        raise ValueError("No puedes enviarte una oferta a ti mismo.")

                    # Regla: jugador -> arquero
                    # Regla: arquero -> jugador
                    if sender_role == "jugador":
                        if cls._validate_role(target_role) != "arquero":
                            raise ValueError("Un jugador solo puede enviar ofertas a un arquero.")

                        if int(match.id_jugador) != sender_user_id:
                            raise PermissionError("Solo puedes ofertar sobre partidos que te pertenecen.")

                        goalkeeper_profile = GoalkeeperRepository.get_profile_by_user_id(db, target_user_id)
                        if not goalkeeper_profile:
                            raise LookupError("El arquero no tiene un perfil público activo.")

                        price = float(goalkeeper_profile.precio)
                        goalkeeper_id = target_user_id
                        player_id = sender_user_id

                    elif sender_role == "arquero":
                        if cls._validate_role(target_role) != "jugador":
                            raise ValueError("Un arquero solo puede enviar ofertas a un jugador.")

                        goalkeeper_profile = GoalkeeperRepository.get_profile_by_user_id(db, sender_user_id)
                        if not goalkeeper_profile:
                            raise LookupError("No tienes un perfil de arquero activo.")

                        price = float(goalkeeper_profile.precio)
                        goalkeeper_id = sender_user_id
                        player_id = target_user_id

                    else:
                        raise PermissionError("Rol no autorizado para crear ofertas.")

                    existing_offer = OfferRepository.get_pending_offer_between(
                        db=db,
                        id_partido=match_id,
                        id_jugador=player_id,
                        id_arquero=goalkeeper_id,
                    )
                    if existing_offer:
                        raise ValueError("Ya existe una oferta pendiente entre estos usuarios para este partido.")

                    offer_data = {
                        "id_partido": match_id,
                        "id_jugador": player_id,
                        "id_arquero": goalkeeper_id,
                        "precio": price,
                        "estado": "pendiente",
                        "created_by_user_id": sender_user_id,
                        "created_by_role": sender_role,
                        "target_user_id": target_user_id,
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
            offers = OfferRepository.list_sent_by_user(db, user_id)
            return offers

    # -----------------------------
    # Listar ofertas recibidas
    # -----------------------------
    @classmethod
    def list_received_offers(cls, current_user: Any) -> List[Any]:
        user_id = cls._get_user_id(current_user)

        with SessionLocal() as db:
            offers = OfferRepository.list_received_by_user(db, user_id)
            return offers

    # -----------------------------
    # Obtener una oferta por ID
    # -----------------------------
    @classmethod
    def get_offer_by_id(cls, current_user: Any, offer_id: int):
        user_id = cls._get_user_id(current_user)

        with SessionLocal() as db:
            offer = OfferRepository.get_by_id(db, offer_id)
            if not offer:
                raise LookupError("La oferta no existe.")

            # Solo pueden verla el creador, el receptor o un administrador si existiera.
            if user_id not in (
                int(offer.created_by_user_id),
                int(offer.target_user_id),
            ):
                raise PermissionError("No tienes permiso para ver esta oferta.")

            return offer

    # -----------------------------
    # Aceptar oferta
    # -----------------------------
    @classmethod
    def accept_offer(cls, current_user: Any, offer_id: int):
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
                    offer = OfferRepository.get_by_id_for_update(db, offer_id)
                    if not offer:
                        raise LookupError("La oferta no existe.")

                    if offer.estado != "pendiente":
                        raise ValueError("Solo se pueden aceptar ofertas pendientes.")

                    if int(offer.target_user_id) != user_id:
                        raise PermissionError("Solo el receptor de la oferta puede aceptarla.")

                    match = MatchRepository.get_by_id_for_update(db, int(offer.id_partido))
                    if not match:
                        raise LookupError("El partido asociado a la oferta no existe.")

                    if match.estado != "sin_arquero":
                        raise ValueError("Este partido ya tiene un arquero asignado.")

                    # Asignación del arquero al partido
                    MatchRepository.assign_goalkeeper(
                        db=db,
                        id_partido=int(match.id_partido),
                        id_arquero_asignado=int(offer.id_arquero),
                    )

                    # Marcar la oferta aceptada
                    OfferRepository.mark_accepted(db, int(offer.id_oferta))

                    # Rechazar las demás ofertas de ese mismo partido
                    OfferRepository.reject_other_offers_for_match(
                        db=db,
                        id_partido=int(match.id_partido),
                        accepted_offer_id=int(offer.id_oferta),
                    )

                    db.flush()

                    return {
                        "message": "Oferta aceptada y arquero asignado correctamente.",
                        "offer_id": int(offer.id_oferta),
                        "match_id": int(match.id_partido),
                        "status": "accepted",
                    }

            except Exception:
                db.rollback()
                raise

    # -----------------------------
    # Rechazar oferta
    # -----------------------------
    @classmethod
    def reject_offer(cls, current_user: Any, offer_id: int):
        """
        Rechaza una oferta.

        Solo el receptor puede rechazarla.
        """
        user_id = cls._get_user_id(current_user)

        with SessionLocal() as db:
            try:
                with db.begin():
                    offer = OfferRepository.get_by_id_for_update(db, offer_id)
                    if not offer:
                        raise LookupError("La oferta no existe.")

                    if int(offer.target_user_id) != user_id:
                        raise PermissionError("Solo el receptor de la oferta puede rechazarla.")

                    if offer.estado != "pendiente":
                        raise ValueError("Solo se pueden rechazar ofertas pendientes.")

                    OfferRepository.mark_rejected(db, int(offer.id_oferta))
                    db.flush()

                    return {
                        "message": "Oferta rechazada correctamente.",
                        "offer_id": int(offer.id_oferta),
                        "status": "rejected",
                    }

            except Exception:
                db.rollback()
                raise