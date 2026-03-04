"""
Auth Router — Giriş, Profil ve Kayıt Endpoint'leri
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Kullanici
from auth import verify_password, get_password_hash, create_access_token, get_current_user
from schemas import LoginRequest, TokenResponse, KullaniciCreate, KullaniciResponse

router = APIRouter(prefix="/api/auth", tags=["Kimlik Doğrulama"])


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Kullanıcı adı ve şifre ile giriş yapar.
    Başarılıysa JWT token ve kullanıcı bilgisi döner.
    """
    # Kullanıcıyı bul
    user = db.query(Kullanici).filter(
        Kullanici.kullanici_adi == request.kullanici_adi
    ).first()

    if not user or not verify_password(request.sifre, user.sifre_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Token oluştur
    access_token = create_access_token(data={"sub": user.kullanici_adi})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "kullanici_adi": user.kullanici_adi,
            "ad_soyad": user.ad_soyad,
            "rol": user.rol,
        }
    }


@router.get("/me", response_model=KullaniciResponse)
def get_profile(current_user: Kullanici = Depends(get_current_user)):
    """
    Mevcut oturumdaki kullanıcının bilgilerini döner.
    Token doğrulaması otomatik yapılır.
    """
    return current_user


@router.post("/register", response_model=KullaniciResponse, status_code=201)
def register(
    kullanici: KullaniciCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """
    Yeni kullanıcı kaydı oluşturur.
    Sadece 'admin' rolündeki kullanıcılar bu endpoint'i kullanabilir.
    """
    # Yetki kontrolü
    if current_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yönetici yetkisi gereklidir."
        )

    # Kullanıcı adı kontrolü
    existing = db.query(Kullanici).filter(
        Kullanici.kullanici_adi == kullanici.kullanici_adi
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu kullanıcı adı zaten kullanımda."
        )

    # Kullanıcı oluştur
    new_user = Kullanici(
        kullanici_adi=kullanici.kullanici_adi,
        sifre_hash=get_password_hash(kullanici.sifre),
        ad_soyad=kullanici.ad_soyad,
        rol=kullanici.rol or "depocu"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user
