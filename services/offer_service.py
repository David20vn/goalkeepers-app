from app.repositories.match_repository import MatchRepository
from app.repositories.offer_repository import OfferRepository

class OfferService:

    @staticmethod
    def create_offer(user_id, data):

        match = MatchRepository.get_by_id(data.id_partido)

        if match.estado != "sin_arquero":
            raise Exception("Partido ya tiene arquero")

        OfferRepository.create(
            match_id=data.id_partido,
            player_id=user_id,
            goalkeeper_id=data.id_arquero
        )