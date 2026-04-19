from app.db import auth_db
from app.core.security import hash_password, verify_password, create_access_token


def _build_token_response(user: dict) -> dict:
    token = create_access_token({"sub": user["id"], "role": user["role"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user["id"],
        "role": user["role"]
    }


async def register(data: dict):
    existing = await auth_db.get_user_by_email(data["email"])
    if existing:
        raise ValueError("Email already registered")

    hashed = hash_password(data["password"])

    user = await auth_db.create_user({
        "name": data["name"],
        "email": data["email"],
        "hashed_password": hashed,
        "role": "user",
    })

    return _build_token_response(user)


async def login(email: str, password: str):
    user = await auth_db.get_user_by_email(email)
    if not user or not verify_password(password, user["password_hash"]):
        raise ValueError("Invalid credentials")

    return _build_token_response(user)