from app.core.database import SessionLocal
from app.models.offer_model import Offer

class OfferRepository:

    @staticmethod
    def create(match_id, player_id, goalkeeper_id):

        db = SessionLocal()

        offer = Offer(
            id_partido=match_id,
            id_jugador=player_id,
            id_arquero=goalkeeper_id
        )

        db.add(offer)
        db.commit()