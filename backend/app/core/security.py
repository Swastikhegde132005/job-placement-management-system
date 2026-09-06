from datetime import datetime, timedelta, timezone
from typing import Optional, Any
import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password[:72], hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password[:72])

def create_access_token(
    subject: Optional[str] = None,
    role: Optional[str] = None,
    data: Optional[dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode: dict[str, Any] = data.copy() if data else {}
    if subject is not None:
        to_encode["sub"] = str(subject)
    if role is not None:
        to_encode["role"] = str(role)

    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
