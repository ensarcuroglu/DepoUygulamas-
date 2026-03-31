"""
Auth Router — Giriş, Çıkış, Profil, Kayıt ve Token Yenileme Endpoint'leri

Clean Architecture (Thin Controller).
Auth cross-cutting concern olarak kalır; Use Case katmanı gerekmez.
İş mantığı doğrudan auth.py utility modülüne delege edilir.
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from database import get_db
from models import Kullanici, SistemLog
from app.core.auth import (
    verify_password,
    get_password_hash,
    hash_token,
    create_access_token,
    create_refresh_token,
    verify_and_get_user_from_refresh_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    ALGORITHM,
)
from app.application.dto.auth_dto import (
    LoginRequestDTO as LoginRequest,
    TokenResponseDTO as TokenResponse,
    KullaniciCreateDTO as KullaniciCreate,
    RefreshRequestDTO as RefreshRequest,
)
from app.application.dto.kullanici_dto import KullaniciResponseDTO as KullaniciResponse
from limiter import limiter

router = APIRouter(prefix="/api/auth", tags=["Kimlik Doğrulama"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, login_request: LoginRequest, db: Session = Depends(get_db)):
    """
    Kullanıcı adı ve şifre ile giriş yapar.
    Başarılıysa kısa ömürlü access_token (8 saat) ve
    uzun ömürlü refresh_token (7 gün) döner.
    """
    user = db.query(Kullanici).filter(
        Kullanici.kullanici_adi == login_request.kullanici_adi
    ).first()

    if not user or not verify_password(login_request.sifre, user.sifre_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanıcı adı veya şifre hatalı.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.kullanici_adi})
    
    # YENİ KOD: Refresh token'ı user.id parametresi ile oluşturuyoruz
    refresh_token = create_refresh_token(user.id)

    # Token formatı "{id}:{raw_token}" olduğu için sadece raw_token kısmını ayırıp hash'liyoruz
    _, raw_token = refresh_token.split(":", 1)
    user.refresh_token_hash = hash_token(raw_token)
    
    user.refresh_token_son_kullanim = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    db.add(SistemLog(
        kullanici_id=user.id,
        islem_tipi="LOGIN",
        modul="Oturum",
        detay=f"{user.ad_soyad} sisteme giriş yaptı."
    ))
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "kullanici_adi": user.kullanici_adi,
            "ad_soyad": user.ad_soyad,
            "rol": user.rol,
            "telefon": user.telefon,
            "email": user.email,
            "departman": user.departman,
            "sicil_no": user.sicil_no,
            "kart_numarasi": user.kart_numarasi,
        }
    }


@router.post("/refresh")
def refresh_token(request: RefreshRequest, db: Session = Depends(get_db)):
    """
    Geçerli bir refresh_token ile yeni access_token üretir.
    Refresh token süresi dolmamışsa ve DB'de kayıtlıysa başarılı olur.
    """
    user = verify_and_get_user_from_refresh_token(request.refresh_token, db)
    new_access_token = create_access_token(data={"sub": user.kullanici_adi})

    return {
        "access_token": new_access_token,
        "token_type": "bearer",
    }


@router.post("/logout", status_code=200)
@limiter.limit("10/minute")
def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user),
):
    """
    Oturumu kapatır ve refresh token'ı sunucu tarafında geçersiz kılar.
    """
    current_user.refresh_token_hash = None
    current_user.refresh_token_son_kullanim = None

    db.add(SistemLog(
        kullanici_id=current_user.id,
        islem_tipi="LOGOUT",
        modul="Oturum",
        detay=f"{current_user.ad_soyad} sistemden çıkış yaptı."
    ))
    db.commit()

    return {"message": "Başarıyla çıkış yapıldı."}


@router.get("/me", response_model=KullaniciResponse)
def get_profile(current_user: Kullanici = Depends(get_current_user)):
    """Mevcut oturumdaki kullanıcının bilgilerini döner."""
    return current_user


@router.post("/register", response_model=KullaniciResponse, status_code=201)
@limiter.limit("3/minute")
def register(
    request: Request,
    kullanici: KullaniciCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """
    Yeni kullanıcı kaydı oluşturur.
    Sadece 'admin' rolündeki kullanıcılar bu endpoint'i kullanabilir.
    """
    if current_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yönetici yetkisi gereklidir."
        )

    existing = db.query(Kullanici).filter(
        Kullanici.kullanici_adi == kullanici.kullanici_adi
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu kullanıcı adı zaten kullanımda."
        )

    new_user = Kullanici(
        kullanici_adi=kullanici.kullanici_adi,
        sifre_hash=get_password_hash(kullanici.sifre),
        ad_soyad=kullanici.ad_soyad,
        rol=kullanici.rol or "depocu",
        telefon=kullanici.telefon,
        email=kullanici.email,
        departman=kullanici.departman,
        sicil_no=kullanici.sicil_no,
        kart_numarasi=kullanici.kart_numarasi
    )
    db.add(new_user)
    db.flush()

    db.add(SistemLog(
        kullanici_id=current_user.id,
        islem_tipi="CREATE",
        modul="Kullanıcı Yönetimi",
        detay=f"Yeni kullanıcı oluşturuldu: {new_user.ad_soyad} ({new_user.kullanici_adi})",
        yeni_veri={"kullanici_adi": new_user.kullanici_adi, "rol": new_user.rol}
    ))
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get("/config")
def get_auth_config():
    """Auth yapılandırma bilgilerini döndürür (hassas bilgi yok)."""
    return {
        "access_token_expire_minutes": ACCESS_TOKEN_EXPIRE_MINUTES,
        "refresh_token_expire_days": REFRESH_TOKEN_EXPIRE_DAYS,
        "algorithm": ALGORITHM,
        "password_hash": "bcrypt",
    }
