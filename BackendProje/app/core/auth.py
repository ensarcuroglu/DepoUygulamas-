"""
JWT authentication helpers.

Creates and verifies access/refresh tokens, hashes passwords, and exposes
FastAPI dependencies for the current user and role checks.
"""

import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from database import get_db
from models import Kullanici
from app.core.config import get_settings
from app.core.constants import AuthConstants


def _get_secret_key() -> str:
    return get_settings().require_jwt_secret_key()


SECRET_KEY = _get_secret_key()
ALGORITHM = get_settings().jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = get_settings().access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = get_settings().refresh_token_expire_days


pwd_context = CryptContext(
    schemes=[AuthConstants.BCRYPT_ALGORITHM],
    deprecated="auto",
)


def _truncate_password(password: str) -> str:
    """Trim passwords to bcrypt's 72-byte input limit."""

    password_bytes = password.encode("utf-8")
    if len(password_bytes) <= 72:
        return password
    truncated = password_bytes[:72]
    return truncated.decode("utf-8", errors="ignore")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(_truncate_password(plain_password), hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(_truncate_password(password))


def hash_token(token: str) -> str:
    return pwd_context.hash(token)


def verify_token(token: str, hashed: str) -> bool:
    return pwd_context.verify(token, hashed)


security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update(
        {
            "exp": expire,
            "type": AuthConstants.ACCESS_TOKEN_TYPE,
            "jti": str(uuid.uuid4()),
        }
    )
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(kullanici_id: int) -> str:
    random_part = secrets.token_urlsafe(32)
    return f"{kullanici_id}:{random_part}"


def verify_and_get_user_from_refresh_token(token: str, db: Session) -> Kullanici:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Geçersiz veya süresi dolmuş oturum. Lütfen tekrar giriş yapın.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        parts = token.split(":", 1)
        if len(parts) != 2:
            raise credentials_exception

        kullanici_id_str, raw_token = parts
        kullanici_id = int(kullanici_id_str)
    except ValueError:
        raise credentials_exception

    matched_user = db.query(Kullanici).filter(Kullanici.id == kullanici_id).first()
    if not matched_user or not matched_user.refresh_token_hash:
        raise credentials_exception

    if not verify_token(raw_token, matched_user.refresh_token_hash):
        raise credentials_exception

    if (
        matched_user.refresh_token_son_kullanim is None
        or datetime.utcnow() > matched_user.refresh_token_son_kullanim
    ):
        raise credentials_exception

    return matched_user


def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Kullanici:
    token = auth.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Oturum doğrulanamadı. Lütfen tekrar giriş yapın.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        kullanici_adi_raw = payload.get("sub")
        token_type_raw = payload.get("type")

        if not isinstance(kullanici_adi_raw, str):
            raise credentials_exception
        if not isinstance(token_type_raw, str):
            raise credentials_exception

        if token_type_raw == AuthConstants.REFRESH_TOKEN_TYPE:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = (
        db.query(Kullanici)
        .filter(Kullanici.kullanici_adi == kullanici_adi_raw)
        .first()
    )
    if user is None:
        raise credentials_exception

    return user


def require_role(*allowed_roles):
    def role_checker(current_user: Kullanici = Depends(get_current_user)):
        if current_user.rol not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu işlem için yetkiniz bulunmamaktadır.",
            )
        return current_user

    return role_checker
