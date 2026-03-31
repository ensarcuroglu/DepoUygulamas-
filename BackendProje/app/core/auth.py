"""
JWT Kimlik Doğrulama Modülü
- Access Token ve Refresh Token oluşturma / doğrulama
- Şifre hash / karşılaştırma
- get_current_user dependency
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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

def _get_secret_key() -> str:
    """JWT Secret Key'i ortam değişkeninden alır, yoksa uygulamayı başlatmaz."""
    key = os.getenv("JWT_SECRET_KEY")
    if not key:
        raise RuntimeError(
            "JWT_SECRET_KEY ortam değişkeni ayarlanmamış! "
            "Lütfen .env dosyasına JWT_SECRET_KEY ekleyin."
        )
    if len(key) < 32:
        raise RuntimeError(
            "JWT_SECRET_KEY en az 32 karakter olmalıdır!"
        )
    return key


SECRET_KEY = _get_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 saat
REFRESH_TOKEN_EXPIRE_DAYS = 7      # 7 gün

# ========================
# ŞİFRE HASHLEME
# ========================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _truncate_password(password: str) -> str:
    """
    Şifreyi bcrypt'in 72 bayt limitine göre kısaltır.
    UTF-8 bayt bazında kesme yapar ve geçerli bir UTF-8 stringi döndürür.
    """
    password_bytes = password.encode("utf-8")
    if len(password_bytes) <= 72:
        return password
    truncated = password_bytes[:72]
    return truncated.decode("utf-8", errors="ignore")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kullanıcının girdiği şifreyi hash ile karşılaştırır (72 bayt sınırına göre kısaltma uygulanır)."""
    return pwd_context.verify(_truncate_password(plain_password), hashed_password)


def get_password_hash(password: str) -> str:
    """Şifreyi bcrypt ile hashler (72 bayt sınırına göre otomatik kısaltma uygulanır)."""
    return pwd_context.hash(_truncate_password(password))


def hash_token(token: str) -> str:
    """Refresh token gibi kısa, sabit uzunluklu token'ları hashler (truncation uygulanmaz)."""
    return pwd_context.hash(token)


def verify_token(token: str, hashed: str) -> bool:
    """Refresh token hash doğrulaması (truncation uygulanmaz)."""
    return pwd_context.verify(token, hashed)


# ========================
# ACCESS TOKEN
# ========================

# Eski OAuth2PasswordBearer kaldırıldı, yerine HTTPBearer eklendi
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """JWT access token oluşturur (kısa ömürlü, 30 dk)."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ========================
# REFRESH TOKEN
# ========================

def create_refresh_token(kullanici_id: int) -> str:
    """
    Kriptografik olarak güvenli, kime ait olduğu bilinen refresh token oluşturur.
    Format: "{kullanici_id}:{rastgele_string}"
    Böylece doğrulama sırasında linear search yerine noktasal arama (O(1)) yapılabilir.
    """
    rastgele_kisim = secrets.token_urlsafe(32)
    return f"{kullanici_id}:{rastgele_kisim}"


def verify_and_get_user_from_refresh_token(token: str, db: Session) -> Kullanici:
    """
    Refresh token'ı doğrular ve ilgili kullanıcıyı döner.
    Format "{kullanici_id}:{rastgele_string}" olduğu için doğrudan ID ile arama yapar.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Geçersiz veya süresi dolmuş oturum. Lütfen tekrar giriş yapın.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Token formatını ayır "{id}:{token}"
        parts = token.split(":", 1)
        if len(parts) != 2:
            raise credentials_exception
        
        kullanici_id_str, raw_token = parts
        kullanici_id = int(kullanici_id_str)
    except ValueError:
        raise credentials_exception

    # ID ile doğrudan kullanıcıyı bul (O(1) lookup)
    eslesen_user = db.query(Kullanici).filter(Kullanici.id == kullanici_id).first()

    if not eslesen_user or not eslesen_user.refresh_token_hash:
        raise credentials_exception

    # Sadece bulunan kullanıcının hash'ini doğrula (Asıl token ile)
    if not verify_token(raw_token, eslesen_user.refresh_token_hash):
        raise credentials_exception

    # Son kullanım tarihi kontrolü
    if eslesen_user.refresh_token_son_kullanim is None or datetime.utcnow() > eslesen_user.refresh_token_son_kullanim:
        raise credentials_exception

    return eslesen_user


# ========================
# DEPENDENCY: Mevcut Kullanıcı
# ========================

def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Kullanici:
    """
    Her korumalı endpoint'te kullanılacak dependency.
    Token'dan kullanıcı adını çözer ve DB'den kullanıcıyı döner.
    """
    # Swagger'dan gelen temiz token
    token = auth.credentials 
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Oturum doğrulanamadı. Lütfen tekrar giriş yapın.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        kullanici_adi: str = payload.get("sub")
        token_type: str = payload.get("type")

        if kullanici_adi is None:
            raise credentials_exception

        # Refresh token Access token'ı yerine kullanılıyor mu? Kontrol et
        if token_type == "refresh":
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