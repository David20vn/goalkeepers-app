from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import hash_password, verify_password, create_access_token
from app.repositories.user_repository import UserRepository
from app.schemas.auth_schema import RegisterRequest


def _build_token_response(user) -> dict:
    return {
        "access_token": create_access_token({"sub": str(user.id), "role": user.role}),
        "token_type": "bearer",
        "user_id": str(user.id),
        "role": user.role,
    }


async def register(db: AsyncSession, data: RegisterRequest):
    repo = UserRepository(db)

    if await repo.get_by_email(data.email):
        raise ValueError("Email already registered")

    user = await repo.create(data, hash_password(data.password))

    await db.commit()
    await db.refresh(user)

    return _build_token_response(user)


async def login(db: AsyncSession, email: str, password: str):
    repo = UserRepository(db)
    user = await repo.get_by_email(email)

    if not user or not verify_password(password, user.password_hash):
        raise ValueError("Invalid credentials")

    return _build_token_response(user)
