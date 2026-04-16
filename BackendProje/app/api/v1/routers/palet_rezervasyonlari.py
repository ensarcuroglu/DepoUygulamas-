"""
Palet Rezervasyonu API Router — Clean Architecture (Thin Controller).
"""

from fastapi import APIRouter, Depends, Header, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.auth import require_role
from app.core.idempotency import idempotency_kontrol, idempotency_kaydet
from database import get_db
from models import Kullanici

from app.infrastructure.di.container import (
    get_rezervasyon_listele_uc,
    get_siparis_rezervasyonlari_uc,
    get_rezervasyon_degistir_uc,
    get_rezervasyon_repo,
)
from app.core.entities.palet_rezervasyonu import RezervasyonDurum
from app.core.exceptions import KayitBulunamadiError, GecersizIslemError
from app.application.dto.palet_rezervasyonu_dto import (
    PaletRezervasyonuResponseDTO,
    RezervasyonIptalRequestDTO,
    RezervasyonDegistirRequestDTO,
)
from app.application.use_cases.palet_rezervasyonu_use_cases import (
    PaletRezervasyonuListeleUseCase,
    SiparisRezervasyonlariGetirUseCase,
    RezervasyonDegistirUseCase,
)

router = APIRouter(prefix="/api/v1/palet-rezervasyonlari", tags=["Palet Rezervasyonları"])


@router.get("/", response_model=List[PaletRezervasyonuResponseDTO])
def rezervasyon_listele(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    durum: Optional[str] = Query(None),
    siparis_id: Optional[int] = Query(None),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: PaletRezervasyonuListeleUseCase = Depends(get_rezervasyon_listele_uc),
):
    return uc.execute(skip=skip, limit=limit, durum=durum, siparis_id=siparis_id)


@router.get("/siparis/{siparis_id}", response_model=List[PaletRezervasyonuResponseDTO])
def siparis_rezervasyonlari(
    siparis_id: int,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: SiparisRezervasyonlariGetirUseCase = Depends(get_siparis_rezervasyonlari_uc),
):
    return uc.execute(siparis_id)


@router.post("/{rezervasyon_id}/iptal", response_model=PaletRezervasyonuResponseDTO)
def rezervasyon_iptal(
    rezervasyon_id: int,
    dto: RezervasyonIptalRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    repo=Depends(get_rezervasyon_repo),
):
    """Tek rezervasyonu manuel iptal eder."""
    rezervasyon = repo.getir_id_ile(rezervasyon_id)
    if not rezervasyon:
        raise KayitBulunamadiError("Rezervasyon", rezervasyon_id)
    if rezervasyon.durum != RezervasyonDurum.AKTIF:
        raise GecersizIslemError("Yalnızca Aktif rezervasyonlar iptal edilebilir.")
    rezervasyon.iptal_et(dto.neden)
    guncellenen = repo.guncelle(rezervasyon)
    return PaletRezervasyonuResponseDTO.from_entity(guncellenen)


@router.post("/{rezervasyon_id}/degistir", response_model=PaletRezervasyonuResponseDTO)
def rezervasyon_degistir(
    rezervasyon_id: int,
    dto: RezervasyonDegistirRequestDTO,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: Kullanici = Depends(require_role("admin")),
    uc: RezervasyonDegistirUseCase = Depends(get_rezervasyon_degistir_uc),
    db: Session = Depends(get_db),
):
    if idempotency_key:
        cached = idempotency_kontrol(db, idempotency_key, "rezervasyon_degistir")
        if cached is not None:
            return cached

    sonuc = uc.execute(
        rezervasyon_id=rezervasyon_id,
        yeni_palet_id=dto.yeni_palet_id,
        kullanici_id=current_user.id,
        neden=dto.neden,
    )

    if idempotency_key:
        idempotency_kaydet(db, idempotency_key, "rezervasyon_degistir",
                           sonuc.model_dump(mode="json"))
    return sonuc
