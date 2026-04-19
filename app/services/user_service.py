from app.db import user_db as user_db

async def get_my_profile(user_id: str):
    user = await user_db.get_user_by_id(user_id)
    if not user:
        raise ValueError("User not found")
    return user

async def update_my_profile(user_id: str, data: dict):
    fields = {k: v for k, v in data.items() if v is not None}
    if not fields:
        raise ValueError("No fields to update")
    return await user_db.update_user(user_id, fields)