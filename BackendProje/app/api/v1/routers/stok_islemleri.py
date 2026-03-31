"""
Stok Islemleri API Router — Palet Bazli Giris/Cikis/Sorgulama (tekli + toplu).

Yeni palet bazli akis icin endpoint'ler.
Mevcut /api/stok-hareketleri/ endpoint'leri dokunulmaz — bu router ayri calisir.
"""

from fastapi import APIRouter, Depends, Request, Header
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

import logging
logger = logging.getLogger(__name__)

from app.core.exceptions import CakismaHatasi

from app.core.auth import require_role
from database import get_db
from models import Kullanici
from limiter import limiter

from app.infrastructure.di.container import (
    get_palet_bazli_stok_service,
    get_palet_sorgulama_service,
)
from app.infrastructure.persistence.mappers import kullanici_to_entity
from app.application.dto.palet_bilgi_dto import PaletBilgiDTO
from app.application.dto.stok_islemleri_dto import (
    PaletGirisRequestDTO,
    PaletCikisRequestDTO,
    TopluPaletGirisRequestDTO,
    TopluPaletCikisRequestDTO,
    TopluIslemResponseDTO,
    TopluIslemPaletSonucDTO,
)
from app.application.dto.stok_hareketi_dto import StokHareketiResponseDTO
from app.core.services.palet_bazli_stok_domain_service import PaletBazliStokDomainService
from app.infrastructure.services.palet_sorgulama_service import PaletSorgulamaService

router = APIRouter(prefix="/api/stok-islemleri", tags=["Stok Islemleri (Palet Bazli)"])


@router.get("/palet/{palet_no}", response_model=PaletBilgiDTO)
@limiter.limit("60/minute")
def palet_sorgula(
    request: Request,
    palet_no: str,
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    service: PaletSorgulamaService = Depends(get_palet_sorgulama_service),
):
    """Palet numarasina gore bilgi getirir. DB veya irsaliye/ERP kaynagindan okur."""
    return service.sorgula(palet_no)


@router.post("/palet-giris", response_model=StokHareketiResponseDTO, status_code=201)
@limiter.limit("30/minute")
def palet_giris(
    request: Request,
    dto: PaletGirisRequestDTO,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    service: PaletBazliStokDomainService = Depends(get_palet_bazli_stok_service),
):
    """Palet numarasi ile stok girisi yapar."""
    kullanici = kullanici_to_entity(current_user)
    
    try:
        hareket = service.palet_giris(dto.palet_no, kullanici)
        db.commit()
        return StokHareketiResponseDTO.from_entity(hareket)
    except IntegrityError:
        # P1 Idempotency: Çakışma durumunda hata dönmek yerine, işlemi zaten 
        # başarılı kabul edip mevcut kaydı dönüyoruz (Idempotent davranış)
        db.rollback()
        logger.warning(f"Idempotency devrede: {dto.palet_no} için mükerrer giriş isteği yakalandı. Key: {idempotency_key}")
        
        mevcut_hareket = service.son_hareketi_getir_palet_ile(dto.palet_no)
        if mevcut_hareket:
            return StokHareketiResponseDTO.from_entity(mevcut_hareket)
            
        raise CakismaHatasi("Palet numarası", dto.palet_no)


@router.post("/palet-cikis", response_model=StokHareketiResponseDTO, status_code=201)
@limiter.limit("30/minute")
def palet_cikis(
    request: Request,
    dto: PaletCikisRequestDTO,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    service: PaletBazliStokDomainService = Depends(get_palet_bazli_stok_service),
):
    """Palet numarasi ile stok cikisi yapar."""
    kullanici = kullanici_to_entity(current_user)
    
    try:
        hareket = service.palet_cikis(
            palet_no=dto.palet_no,
            kullanici=kullanici,
            miktar=dto.miktar,
            siparis_no=dto.siparis_no,
            aciklama=dto.aciklama,
        )
        db.commit()
        return StokHareketiResponseDTO.from_entity(hareket)
    except IntegrityError:
        # Çıkış sırasında da yaşanabilecek bir veri tabanı kilidi çakışmasını engelle
        db.rollback()
        raise CakismaHatasi("Palet çıkış işlemi", dto.palet_no)


# ─────────────────────────────────────────
# TOPLU İŞLEM ENDPOİNT'LERİ (Faz 2)
# ─────────────────────────────────────────


def _sonuclari_dto_ya_cevir(sonuclar) -> TopluIslemResponseDTO:
    """Domain service sonuclarini response DTO'ya cevirir."""
    dto_sonuclar = [
        TopluIslemPaletSonucDTO(
            palet_no=s.palet_no,
            basarili=s.basarili,
            hata_mesaji=s.hata_mesaji,
            hareket_id=s.hareket.id if s.hareket else None,
        )
        for s in sonuclar
    ]
    basarili = sum(1 for s in sonuclar if s.basarili)
    return TopluIslemResponseDTO(
        toplam=len(sonuclar),
        basarili=basarili,
        basarisiz=len(sonuclar) - basarili,
        sonuclar=dto_sonuclar,
    )


@router.post("/toplu-giris", response_model=TopluIslemResponseDTO)
@limiter.limit("10/minute")
def toplu_palet_giris(
    request: Request,
    dto: TopluPaletGirisRequestDTO,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    service: PaletBazliStokDomainService = Depends(get_palet_bazli_stok_service),
):
    """Birden fazla paleti tek seferde giris yapar. Pre-validation + all-or-nothing."""
    kullanici = kullanici_to_entity(current_user)

    sonuclar = service.toplu_palet_giris(dto.palet_no_listesi, kullanici)

    # Hata varsa commit yapma (pre-validation basarisiz)
    if any(not s.basarili for s in sonuclar):
        db.rollback()
        return _sonuclari_dto_ya_cevir(sonuclar)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise CakismaHatasi("Toplu palet girişi", ", ".join(dto.palet_no_listesi[:3]))

    # Kaynak onayini transaction commit sonrasina tasiyoruz
    try:
        service.toplu_palet_giris_kaynagini_onayla(dto.palet_no_listesi)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return _sonuclari_dto_ya_cevir(sonuclar)


@router.post("/toplu-cikis", response_model=TopluIslemResponseDTO)
@limiter.limit("10/minute")
def toplu_palet_cikis(
    request: Request,
    dto: TopluPaletCikisRequestDTO,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    service: PaletBazliStokDomainService = Depends(get_palet_bazli_stok_service),
):
    """Birden fazla paletten tek seferde cikis yapar. Pre-validation + all-or-nothing."""
    kullanici = kullanici_to_entity(current_user)

    kalemler = [
        {"palet_no": k.palet_no, "miktar": k.miktar}
        for k in dto.kalemler
    ]

    sonuclar = service.toplu_palet_cikis(
        kalemler=kalemler,
        kullanici=kullanici,
        siparis_no=dto.siparis_no,
        aciklama=dto.aciklama,
    )

    if any(not s.basarili for s in sonuclar):
        db.rollback()
        return _sonuclari_dto_ya_cevir(sonuclar)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        palet_nolar = [k.palet_no for k in dto.kalemler[:3]]
        raise CakismaHatasi("Toplu palet çıkışı", ", ".join(palet_nolar))

    return _sonuclari_dto_ya_cevir(sonuclar)
