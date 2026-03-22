from fastapi import APIRouter, Depends
from app.schemas.offer_schema import OfferCreate
from app.services.offer_service import OfferService

router = APIRouter(prefix="/offers")

@router.post("/")
def create_offer(data: OfferCreate, user_id: int = Depends(get_current_user)):
    return OfferService.create_offer(user_id, data)