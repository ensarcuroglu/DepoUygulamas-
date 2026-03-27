"""
Stok Islemleri API Router — Palet Bazli Giris/Cikis/Sorgulama.

Yeni palet bazli akis icin endpoint'ler.
Mevcut /api/stok-hareketleri/ endpoint'leri dokunulmaz — bu router ayri calisir.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from auth import require_role
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
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    service: PaletBazliStokDomainService = Depends(get_palet_bazli_stok_service),
):
    """Palet numarasi ile stok girisi yapar.

    Irsaliye'deki palet bilgisini referans alarak lot + palet + stok hareketi olusturur.
    """
    kullanici = kullanici_to_entity(current_user)
    hareket = service.palet_giris(dto.palet_no, kullanici)
    db.commit()
    return StokHareketiResponseDTO.from_entity(hareket)


@router.post("/palet-cikis", response_model=StokHareketiResponseDTO, status_code=201)
@limiter.limit("30/minute")
def palet_cikis(
    request: Request,
    dto: PaletCikisRequestDTO,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    service: PaletBazliStokDomainService = Depends(get_palet_bazli_stok_service),
):
    """Palet numarasi ile stok cikisi yapar.

    miktar bos ise tam cikis, dolu ise kismi cikis yapilir.
    """
    kullanici = kullanici_to_entity(current_user)
    hareket = service.palet_cikis(
        palet_no=dto.palet_no,
        kullanici=kullanici,
        miktar=dto.miktar,
        siparis_no=dto.siparis_no,
        aciklama=dto.aciklama,
    )
    db.commit()
    return StokHareketiResponseDTO.from_entity(hareket)
