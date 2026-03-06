"""
Auth Router — Giriş, Profil ve Kayıt Endpoint'leri
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Kullanici, SistemLog
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

    # Sisteme giriş logu
    yeni_log = SistemLog(
        kullanici_id=user.id,
        islem_tipi="LOGIN",
        modul="Oturum",
        detay=f"{user.ad_soyad} sisteme giriş yaptı."
    )
    db.add(yeni_log)
    db.commit()

    return {
        "access_token": access_token,
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
        rol=kullanici.rol or "depocu",
        telefon=kullanici.telefon,
        email=kullanici.email,
        departman=kullanici.departman,
        sicil_no=kullanici.sicil_no,
        kart_numarasi=kullanici.kart_numarasi
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Log Kaydı
    yeni_log = SistemLog(
        kullanici_id=current_user.id,
        islem_tipi="CREATE",
        modul="Kullanıcı Yönetimi",
        detay=f"Yeni kullanıcı oluşturuldu: {new_user.ad_soyad} ({new_user.kullanici_adi})",
        yeni_veri={"kullanici_adi": new_user.kullanici_adi, "rol": new_user.rol}
    )
    db.add(yeni_log)
    db.commit()

    return new_user
