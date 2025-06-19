import jwt
from datetime import datetime, timedelta
from app.config import settings
from typing import Optional

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