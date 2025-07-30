import jwt
from datetime import datetime, timedelta
from app.config import settings
from typing import Optional
from aiohttp import web

from app.database.db import engine
from app.database.models import Users
from sqlalchemy import select


def create_access_token(data: dict, expires_delta: Optional[int] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(seconds=expires_delta or settings.JWT_EXP_SECONDS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        decoded = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return decoded
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.PyJWTError:
        raise ValueError("Invalid token")


def get_jwt_payload(request: web.Request) -> dict:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise web.HTTPUnauthorized(reason="Missing or invalid Authorization header")

    token = auth_header[7:]
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise web.HTTPUnauthorized(reason="JWT expired")
    except jwt.InvalidTokenError:
        raise web.HTTPUnauthorized(reason="Invalid JWT token")

    return payload


async def get_user_from_token(token: str):
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
        if not user_id:
            return None

        async with engine.connect() as conn:
            result = await conn.execute(select(Users).where(Users.c.user_id == user_id))
            return result.fetchone()
    except Exception:
        return None

