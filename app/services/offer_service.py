# app/services/offer_service.py

from contextlib import contextmanager
from typing import Any, List, Optional

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.offer import Offer
from app.models.match import Match
from app.models.goalkeeper_profile import GoalkeeperProfile
from app.models.user import User
from app.schemas.offer import OfferCreate, OfferRead, OfferActionResponse


class OfferService:
    """
    Servicio de ofertas.

    Supone que la tabla 'ofertas' tiene, al menos, estos campos:
    - id_oferta
    - id_partido
    - id_jugador
    - id_arquero
    - id_emisor  -> para saber quién creó la oferta
    - precio
    - estado
    - fecha_oferta

    Estados esperados:
    - pendiente
    - aceptada
    - rechazada
    """

    # =========================
    # Helpers internos
    # =========================

    @staticmethod
    @contextmanager
    def _session_scope():
        db: Session = SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _get_attr(obj: Any, *names: str, default: Any = None) -> Any:
        """
        Intenta leer un atributo de un objeto con varios nombres posibles.
        Útil cuando aún no tienes exactamente iguales los nombres en todos los modelos.
        """
        for name in names:
            if hasattr(obj, name):
                return getattr(obj, name)
        return default

    @staticmethod
    def _current_user_id(current_user: Any) -> int:
        user_id = OfferService._get_attr(current_user, "id_usuario", "id", "user_id")
        if user_id is None:
            raise ValueError("No se pudo obtener el id del usuario autenticado.")
        return int(user_id)

    @staticmethod
    def _current_user_role(current_user: Any) -> str:
        role = OfferService._get_attr(
            current_user,
            "tipo_usuario",
            "rol",
            "role",
            "user_type",
        )
        if role is None:
            raise ValueError("No se pudo obtener el rol del usuario autenticado.")
        return str(role).lower()

    @staticmethod
    def _to_offer_read(offer: Offer) -> OfferRead:
        # Asume Pydantic v2 con from_attributes=True en OfferRead
        return OfferRead.model_validate(offer, from_attributes=True)

    @staticmethod
    def _receiver_user_id(offer: Offer) -> int:
        """
        Si el emisor fue el jugador, el receptor es el arquero.
        Si el emisor fue el arquero, el receptor es el jugador.
        """
        emisor_id = OfferService._get_attr(offer, "id_emisor")
        if emisor_id is None:
            raise ValueError("La oferta no tiene id_emisor. Agrega ese campo al modelo/tabla.")

        id_jugador = OfferService._get_attr(offer, "id_jugador")
        id_arquero = OfferService._get_attr(offer, "id_arquero")

        if emisor_id == id_jugador:
            return int(id_arquero)
        return int(id_jugador)

    @staticmethod
    def _ensure_user_can_view_offer(current_user: Any, offer: Offer) -> None:
        user_id = OfferService._current_user_id(current_user)
        id_jugador = OfferService._get_attr(offer, "id_jugador")
        id_arquero = OfferService._get_attr(offer, "id_arquero")
        id_emisor = OfferService._get_attr(offer, "id_emisor")

        if user_id not in {int(id_jugador), int(id_arquero), int(id_emisor)}:
            raise PermissionError("No tienes permisos para ver esta oferta.")

    @staticmethod
    def _ensure_only_receiver_can_act(current_user: Any, offer: Offer) -> None:
        user_id = OfferService._current_user_id(current_user)
        receiver_id = OfferService._receiver_user_id(offer)

        if user_id != receiver_id:
            raise PermissionError("Solo el receptor de la oferta puede aceptarla o rechazarla.")

    # =========================
    # Creación de oferta
    # =========================

    @staticmethod
    def create_offer(current_user: Any, payload: OfferCreate) -> OfferRead:
        """
        Crea una oferta.
        Soporta dos escenarios:
        1) Jugador ofrece a un arquero para uno de sus partidos.
        2) Arquero propone su servicio sobre un partido publicado.

        Reglas:
        - Si el usuario autenticado es jugador, debe indicar id_partido e id_arquero.
        - Si el usuario autenticado es arquero, debe indicar al menos id_partido.
        - El precio siempre sale del perfil del arquero.
        - El partido debe seguir sin arquero.
        - No se permiten ofertas duplicadas activas sobre la misma pareja (partido + arquero).
        """
        user_id = OfferService._current_user_id(current_user)
        role = OfferService._current_user_role(current_user)

        id_partido = OfferService._get_attr(payload, "id_partido")
        id_arquero_payload = OfferService._get_attr(payload, "id_arquero", default=None)

        if id_partido is None:
            raise ValueError("Debes indicar id_partido.")

        with OfferService._session_scope() as db:
            try:
                # Bloqueamos el partido para leerlo de forma segura
                match = (
                    db.execute(
                        select(Match).where(Match.id_partido == id_partido).with_for_update()
                    )
                    .scalar_one_or_none()
                )

                if match is None:
                    raise LookupError("El partido no existe.")

                estado_partido = OfferService._get_attr(match, "estado")
                id_jugador_partido = OfferService._get_attr(match, "id_jugador")

                if estado_partido != "sin_arquero":
                    raise ValueError("No se pueden crear ofertas sobre un partido ya asignado.")

                # Determinar quién es el arquero objetivo y quién es el jugador del partido
                if role == "jugador":
                    if id_arquero_payload is None:
                        raise ValueError("Como jugador debes indicar id_arquero.")

                    if int(id_jugador_partido) != user_id:
                        raise PermissionError("No puedes hacer ofertas sobre partidos que no te pertenecen.")

                    id_arquero = int(id_arquero_payload)
                    id_jugador = user_id
                    id_emisor = user_id

                elif role == "arquero":
                    # El arquero propone su perfil sobre un partido abierto
                    id_arquero = user_id
                    id_jugador = int(id_jugador_partido)
                    id_emisor = user_id

                    if id_arquero_payload is not None and int(id_arquero_payload) != user_id:
                        raise PermissionError("El arquero autenticado no coincide con id_arquero enviado.")

                else:
                    raise PermissionError("Tu tipo de usuario no está autorizado para crear ofertas.")

                # Validar que el arquero exista y tenga perfil
                goalkeeper_profile = (
                    db.execute(
                        select(GoalkeeperProfile).where(
                            GoalkeeperProfile.id_usuario == id_arquero
                        )
                    )
                    .scalar_one_or_none()
                )

                if goalkeeper_profile is None:
                    raise LookupError("El arquero no tiene perfil registrado.")

                precio = OfferService._get_attr(goalkeeper_profile, "precio")
                if precio is None:
                    raise ValueError("El perfil del arquero no tiene precio definido.")

                # Evitar duplicados activos para la misma pareja partido + arquero
                existing_offer = (
                    db.execute(
                        select(Offer).where(
                            Offer.id_partido == id_partido,
                            Offer.id_arquero == id_arquero,
                            Offer.estado.in_(["pendiente", "aceptada"]),
                        )
                    )
                    .scalar_one_or_none()
                )

                if existing_offer is not None:
                    raise ValueError("Ya existe una oferta activa para este partido y este arquero.")

                new_offer = Offer(
                    id_partido=id_partido,
                    id_jugador=id_jugador,
                    id_arquero=id_arquero,
                    id_emisor=id_emisor,
                    precio=precio,
                    estado="pendiente",
                )

                db.add(new_offer)
                db.flush()
                db.refresh(new_offer)

                return OfferService._to_offer_read(new_offer)

            except (LookupError, ValueError, PermissionError):
                raise
            except SQLAlchemyError as exc:
                raise RuntimeError(f"Error de base de datos al crear la oferta: {exc}") from exc

    # =========================
    # Listados
    # =========================

    @staticmethod
    def list_sent_offers(current_user: Any) -> List[OfferRead]:
        """
        Devuelve las ofertas enviadas por el usuario autenticado.
        Requiere el campo id_emisor en la tabla of ofertas.
        """
        user_id = OfferService._current_user_id(current_user)

        with OfferService._session_scope() as db:
            try:
                offers = (
                    db.execute(
                        select(Offer)
                        .where(Offer.id_emisor == user_id)
                        .order_by(Offer.fecha_oferta.desc())
                    )
                    .scalars()
                    .all()
                )
                return [OfferService._to_offer_read(offer) for offer in offers]
            except SQLAlchemyError as exc:
                raise RuntimeError(f"Error al listar ofertas enviadas: {exc}") from exc

    @staticmethod
    def list_received_offers(current_user: Any) -> List[OfferRead]:
        """
        Devuelve las ofertas recibidas por el usuario autenticado.
        Se consideran recibidas las ofertas donde el usuario participa,
        pero no fue el emisor.
        """
        user_id = OfferService._current_user_id(current_user)

        with OfferService._session_scope() as db:
            try:
                offers = (
                    db.execute(
                        select(Offer)
                        .where(
                            ((Offer.id_jugador == user_id) | (Offer.id_arquero == user_id)),
                            Offer.id_emisor != user_id,
                        )
                        .order_by(Offer.fecha_oferta.desc())
                    )
                    .scalars()
                    .all()
                )
                return [OfferService._to_offer_read(offer) for offer in offers]
            except SQLAlchemyError as exc:
                raise RuntimeError(f"Error al listar ofertas recibidas: {exc}") from exc

    # =========================
    # Consulta puntual
    # =========================

    @staticmethod
    def get_offer_by_id(current_user: Any, offer_id: int) -> OfferRead:
        """
        Devuelve una oferta por ID solo si el usuario autenticado tiene permiso.
        """
        with OfferService._session_scope() as db:
            try:
                offer = (
                    db.execute(
                        select(Offer).where(Offer.id_oferta == offer_id)
                    )
                    .scalar_one_or_none()
                )

                if offer is None:
                    raise LookupError("La oferta no existe.")

                OfferService._ensure_user_can_view_offer(current_user, offer)
                return OfferService._to_offer_read(offer)

            except (LookupError, PermissionError):
                raise
            except SQLAlchemyError as exc:
                raise RuntimeError(f"Error al consultar la oferta: {exc}") from exc

    # =========================
    # Aceptar / rechazar
    # =========================

    @staticmethod
    def accept_offer(current_user: Any, offer_id: int) -> OfferActionResponse:
        """
        Acepta una oferta usando una transacción atómica.

        Flujo:
        1. Bloquear la oferta.
        2. Validar que esté pendiente.
        3. Validar que el usuario autenticado sea el receptor.
        4. Bloquear el partido.
        5. Verificar que siga sin arquero.
        6. Asignar arquero al partido.
        7. Marcar la oferta como aceptada.
        8. Rechazar las demás ofertas pendientes del mismo partido.
        """
        with OfferService._session_scope() as db:
            try:
                with db.begin():
                    offer = (
                        db.execute(
                            select(Offer)
                            .where(Offer.id_oferta == offer_id)
                            .with_for_update()
                        )
                        .scalar_one_or_none()
                    )

                    if offer is None:
                        raise LookupError("La oferta no existe.")

                    OfferService._ensure_only_receiver_can_act(current_user, offer)

                    estado_oferta = OfferService._get_attr(offer, "estado")
                    if estado_oferta != "pendiente":
                        raise ValueError("Solo se pueden aceptar ofertas pendientes.")

                    match_id = OfferService._get_attr(offer, "id_partido")
                    match = (
                        db.execute(
                            select(Match)
                            .where(Match.id_partido == match_id)
                            .with_for_update()
                        )
                        .scalar_one_or_none()
                    )

                    if match is None:
                        raise LookupError("El partido asociado a la oferta no existe.")

                    estado_partido = OfferService._get_attr(match, "estado")
                    if estado_partido != "sin_arquero":
                        raise ValueError("El partido ya fue asignado y no puede aceptar más ofertas.")

                    # Asignar arquero al partido
                    match.id_arquero_asignado = OfferService._get_attr(offer, "id_arquero")
                    match.estado = "asignado"

                    # Aceptar esta oferta
                    offer.estado = "aceptada"

                    # Rechazar automáticamente las demás ofertas del mismo partido
                    db.execute(
                        update(Offer)
                        .where(
                            Offer.id_partido == match_id,
                            Offer.id_oferta != offer.id_oferta,
                            Offer.estado == "pendiente",
                        )
                        .values(estado="rechazada")
                    )

                db.refresh(offer)

                return OfferActionResponse(
                    success=True,
                    message="Oferta aceptada y arquero asignado correctamente.",
                    offer_id=OfferService._get_attr(offer, "id_oferta"),
                    status=OfferService._get_attr(offer, "estado"),
                    match_id=OfferService._get_attr(offer, "id_partido"),
                )

            except (LookupError, ValueError, PermissionError):
                raise
            except SQLAlchemyError as exc:
                raise RuntimeError(f"Error de base de datos al aceptar la oferta: {exc}") from exc

    @staticmethod
    def reject_offer(current_user: Any, offer_id: int) -> OfferActionResponse:
        """
        Rechaza una oferta. Solo el receptor puede hacerlo.
        """
        with OfferService._session_scope() as db:
            try:
                with db.begin():
                    offer = (
                        db.execute(
                            select(Offer)
                            .where(Offer.id_oferta == offer_id)
                            .with_for_update()
                        )
                        .scalar_one_or_none()
                    )

                    if offer is None:
                        raise LookupError("La oferta no existe.")

                    OfferService._ensure_only_receiver_can_act(current_user, offer)

                    if OfferService._get_attr(offer, "estado") != "pendiente":
                        raise ValueError("Solo se pueden rechazar ofertas pendientes.")

                    offer.estado = "rechazada"

                db.refresh(offer)

                return OfferActionResponse(
                    success=True,
                    message="Oferta rechazada correctamente.",
                    offer_id=OfferService._get_attr(offer, "id_oferta"),
                    status=OfferService._get_attr(offer, "estado"),
                    match_id=OfferService._get_attr(offer, "id_partido"),
                )

            except (LookupError, ValueError, PermissionError):
                raise
            except SQLAlchemyError as exc:
                raise RuntimeError(f"Error de base de datos al rechazar la oferta: {exc}") from exc