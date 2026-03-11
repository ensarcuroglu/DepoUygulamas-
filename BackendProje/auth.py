"""
JWT Kimlik Doğrulama Modülü
- Access Token ve Refresh Token oluşturma / doğrulama
- Şifre hash / karşılaştırma
- get_current_user dependency
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import os
import secrets

from database import get_db
from models import Kullanici

# ========================
# YAPILANDIRMA
# ========================

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "depo-yonetim-sistemi-gizli-anahtar-2026-uretim-ortaminda-degistirin")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30   # 30 dakika
REFRESH_TOKEN_EXPIRE_DAYS = 7      # 7 gün

# ========================
# ŞİFRE HASHLEME
# ========================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kullanıcının girdiği şifreyi hash ile karşılaştırır."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Şifreyi bcrypt ile hashler."""
    return pwd_context.hash(password)


# ========================
# ACCESS TOKEN
# ========================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """JWT access token oluşturur (kısa ömürlü, 30 dk)."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ========================
# REFRESH TOKEN
# ========================

def create_refresh_token(data: dict) -> str:
    """
    JWT refresh token oluşturur (uzun ömürlü, 7 gün).
    İçinde rastgele jti (JWT ID) bulunur — her token benzersizdir.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    jti = secrets.token_hex(16)  # Benzersiz token ID
    to_encode.update({"exp": expire, "type": "refresh", "jti": jti})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_and_get_user_from_refresh_token(token: str, db: Session) -> Kullanici:
    """
    Refresh token'ı doğrular ve ilgili kullanıcıyı döner.
    1. JWT imzasını doğrular
    2. Token tipini kontrol eder (type == "refresh")
    3. DB'den kullanıcıyı bulur
    4. DB'deki hash ile karşılaştırır (revocation kontrolü)
    5. Son kullanım tarihini kontrol eder
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Geçersiz veya süresi dolmuş oturum. Lütfen tekrar giriş yapın.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        kullanici_adi: str = payload.get("sub")
        token_type: str = payload.get("type")

        if kullanici_adi is None or token_type != "refresh":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # DB'den kullanıcıyı bul
    user = db.query(Kullanici).filter(Kullanici.kullanici_adi == kullanici_adi).first()
    if user is None:
        raise credentials_exception

    # Refresh token DB'de kayıtlı mı? (revocation kontrolü)
    if user.refresh_token_hash is None:
        raise credentials_exception

    # Hash eşleşmesi — token hâlâ geçerli mi?
    if not pwd_context.verify(token, user.refresh_token_hash):
        raise credentials_exception

    # Son kullanım tarihi kontrolü
    if user.refresh_token_son_kullanim is None or datetime.utcnow() > user.refresh_token_son_kullanim:
        raise credentials_exception

    return user


# ========================
# DEPENDENCY: Mevcut Kullanıcı
# ========================

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Kullanici:
    """
    Her korumalı endpoint'te kullanılacak dependency.
    Token'dan kullanıcı adını çözer ve DB'den kullanıcıyı döner.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Oturum doğrulanamadı. Lütfen tekrar giriş yapın.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        kullanici_adi: str = payload.get("sub")
        if kullanici_adi is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(Kullanici).filter(Kullanici.kullanici_adi == kullanici_adi).first()
    if user is None:
        raise credentials_exception

    return user


# ========================
# ROL TABANLI YETKİLENDİRME
# ========================

def require_role(*allowed_roles):
    """
    Belirli rollere erişimi kısıtlayan dependency factory.
    Kullanım: Depends(require_role("admin")) veya Depends(require_role("admin", "depocu"))
    """
    def role_checker(current_user: Kullanici = Depends(get_current_user)):
        if current_user.rol not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bu işlem için yetkiniz bulunmamaktadır."
            )
        return current_user
    return role_checker
