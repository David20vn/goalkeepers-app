from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.schemas.user_schema import UserUpdate
from uuid import UUID


async def get_my_profile(db: AsyncSession, user_id: UUID):
    user = await UserRepository(db).get_by_id(user_id)
    if not user:
        raise ValueError("User not found")
    return user


async def update_my_profile(db: AsyncSession, user_id: UUID, data: UserUpdate):
    user = await UserRepository(db).update(user_id, data)
    if not user:
        raise ValueError("No fields to update")
    await db.commit()
    await db.refresh(user)
    return user
