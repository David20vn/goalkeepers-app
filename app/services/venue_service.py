from app.repositories.venue_repository import VenueRepository

class VenueService:
    def __init__(self, session):
        self.venue_repo = VenueRepository(session)

    async def create_venue(self, payload):
        data = {
            "name": payload.name,
            "address": payload.address,
            "latitude": payload.latitude,
            "longitude": payload.longitude,
        }
        return await self.venue_repo.create(data)

    async def get_venue(self, venue_id):
        venue = await self.venue_repo.get_by_id(venue_id)
        if not venue:
            raise LookupError("Venue not found")
        return venue

    async def list_venues(self):
        return await self.venue_repo.list_all()