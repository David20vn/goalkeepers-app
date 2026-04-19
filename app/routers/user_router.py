from fastapi import APIRouter
from fastapi import Depends, HTTPException
from app.schemas.user_schema import UserResponse, UserUpdate
from app.dependencies import get_current_user
from app.services import user_service as user_service


router = APIRouter(prefix="/user", tags=["user"])

@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user=Depends(get_current_user)):
    try:
        user = await user_service.get_my_profile(current_user["id"])
        return user
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/me", response_model=UserResponse)
async def update_my_profile(data: UserUpdate, current_user=Depends(get_current_user)):
    try:
        return await user_service.update_my_profile(current_user["id"], data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))