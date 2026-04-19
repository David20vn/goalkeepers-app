from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = decode_token(token)
        return {"id": payload["sub"], "role": payload["role"]}
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")