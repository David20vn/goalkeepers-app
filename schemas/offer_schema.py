from pydantic import BaseModel

class OfferCreate(BaseModel):
    id_partido: int
    id_arquero: int