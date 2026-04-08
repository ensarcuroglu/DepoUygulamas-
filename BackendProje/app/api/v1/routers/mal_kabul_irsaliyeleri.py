from fastapi import APIRouter, Depends, Query
from typing import Optional, List

from app.core.auth import require_role
from models import Kullanici

from app.infrastructure.di.container import (
    get_mal_kabul_irsaliye_listele_uc,
    get_mal_kabul_irsaliye_getir_uc,
    get_mal_kabul_irsaliye_olustur_uc,
    get_mal_kabul_irsaliye_guncelle_uc,
    get_mal_kabul_irsaliye_sil_uc,
    get_irsaliye_onayla_ve_gorev_olustur_uc,
)

from app.application.dto import (
    MalKabulIrsaliyeOlusturRequestDTO,
    MalKabulIrsaliyeGuncelleRequestDTO,
    MalKabulIrsaliyeResponseDTO,
)

from app.application.use_cases import (
    MalKabulIrsaliyeListeleUseCase,
    MalKabulIrsaliyeGetirUseCase,
    MalKabulIrsaliyeOlusturUseCase,
    MalKabulIrsaliyeGuncelleUseCase,
    MalKabulIrsaliyeSilUseCase,
    IrsaliyeOnaylaVeGorevOlusturUseCase,
)


router = APIRouter(prefix="/api/mal-kabul-irsaliyeleri", tags=["Mal Kabul İrsaliyeleri"])


@router.get("/", response_model=List[MalKabulIrsaliyeResponseDTO])
def mal_kabul_irsaliyeleri_listele(
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    durum: Optional[str] = Query(None),
    arama: Optional[str] = Query(None),
    depo_id: Optional[int] = Query(None),
    tedarikci_id: Optional[int] = Query(None),
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    uc: MalKabulIrsaliyeListeleUseCase = Depends(get_mal_kabul_irsaliye_listele_uc),
):
    """Mal kabul irsaliyelerini listeler."""
    return uc.execute(
        skip=skip, limit=limit, durum=durum, arama=arama,
        depo_id=depo_id, tedarikci_id=tedarikci_id,
    )


@router.get("/{irsaliye_id}", response_model=MalKabulIrsaliyeResponseDTO)
def mal_kabul_irsaliye_detay(
    irsaliye_id: int,
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    uc: MalKabulIrsaliyeGetirUseCase = Depends(get_mal_kabul_irsaliye_getir_uc),
):
    """Mal kabul irsaliyesi detayını getirir."""
    return uc.execute(irsaliye_id)


@router.post("/", response_model=MalKabulIrsaliyeResponseDTO, status_code=201)
def mal_kabul_irsaliye_ekle(
    irsaliye: MalKabulIrsaliyeOlusturRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "depocu")),
    uc: MalKabulIrsaliyeOlusturUseCase = Depends(get_mal_kabul_irsaliye_olustur_uc),
):
    """Yeni mal kabul irsaliyesi oluşturur. Otomatik numara atar (MKI-YYYY-NNNNN)."""
    return uc.execute(irsaliye, kullanici_id=current_user.id)


@router.put("/{irsaliye_id}", response_model=MalKabulIrsaliyeResponseDTO)
def mal_kabul_irsaliye_guncelle(
    irsaliye_id: int,
    irsaliye_update: MalKabulIrsaliyeGuncelleRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "depocu")),
    uc: MalKabulIrsaliyeGuncelleUseCase = Depends(get_mal_kabul_irsaliye_guncelle_uc),
):
    """Mal kabul irsaliyesini günceller ve durum geçişlerini yönetir."""
    return uc.execute(irsaliye_id, irsaliye_update, kullanici_id=current_user.id)


@router.delete("/{irsaliye_id}")
def mal_kabul_irsaliye_sil(
    irsaliye_id: int,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: MalKabulIrsaliyeSilUseCase = Depends(get_mal_kabul_irsaliye_sil_uc),
):
    """Taslak mal kabul irsaliyesini siler."""
    uc.execute(irsaliye_id, kullanici_id=current_user.id)
    return {"detail": "İrsaliye silindi"}

@router.post("/{irsaliye_id}/onayla", response_model=MalKabulIrsaliyeResponseDTO)
def mal_kabul_irsaliye_onayla(
    irsaliye_id: int,
    current_user: Kullanici = Depends(require_role("admin", "depocu")),
    uc: IrsaliyeOnaylaVeGorevOlusturUseCase = Depends(get_irsaliye_onayla_ve_gorev_olustur_uc),
):
    """Taslak irsaliyeyi onaylar, paletleri oluşturur ve yerleştirme görevlerini atar."""
    return uc.execute(irsaliye_id, kullanici_id=current_user.id)
