"""
Sevkiyat Planlama API Router — Clean Architecture (Thin Controller).
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from datetime import date

from auth import require_role
from models import Kullanici

from app.infrastructure.di.container import (
    get_sevkiyat_listele_uc,
    get_sevkiyat_getir_uc,
    get_sevkiyat_olustur_uc,
    get_sevkiyat_guncelle_uc,
    get_sevkiyat_sil_uc,
)

from app.application.dto import (
    SevkiyatPlaniOlusturRequestDTO,
    SevkiyatPlaniGuncelleRequestDTO,
    SevkiyatPlaniResponseDTO,
)

from app.application.use_cases import (
    SevkiyatPlaniListeleUseCase,
    SevkiyatPlaniGetirUseCase,
    SevkiyatPlaniOlusturUseCase,
    SevkiyatPlaniGuncelleUseCase,
    SevkiyatPlaniSilUseCase,
)

router = APIRouter(prefix="/api/sevkiyat-planlama", tags=["Sevkiyat Planlama"])


@router.get("/", response_model=List[SevkiyatPlaniResponseDTO])
def sevkiyat_planlari_listele(
    skip: int = 0,
    limit: int = 100,
    durum: Optional[str] = Query(None),
    tarih_baslang: Optional[date] = Query(None),
    tarih_bitis: Optional[date] = Query(None),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: SevkiyatPlaniListeleUseCase = Depends(get_sevkiyat_listele_uc),
):
    """Sevkiyat planlarını listeler. Durum ve tarih filtresi destekler."""
    return uc.execute(
        skip=skip, limit=limit, durum=durum,
        tarih_baslang=tarih_baslang, tarih_bitis=tarih_bitis,
    )


@router.get("/{plan_id}", response_model=SevkiyatPlaniResponseDTO)
def sevkiyat_plani_detay(
    plan_id: int,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: SevkiyatPlaniGetirUseCase = Depends(get_sevkiyat_getir_uc),
):
    """Tek sevkiyat planı detay bilgisini döner."""
    return uc.execute(plan_id)


@router.post("/", response_model=SevkiyatPlaniResponseDTO, status_code=201)
def sevkiyat_plani_ekle(
    plan: SevkiyatPlaniOlusturRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: SevkiyatPlaniOlusturUseCase = Depends(get_sevkiyat_olustur_uc),
):
    """Yeni sevkiyat planı oluşturur."""
    return uc.execute(plan, kullanici_id=current_user.id)


@router.put("/{plan_id}", response_model=SevkiyatPlaniResponseDTO)
def sevkiyat_plani_guncelle(
    plan_id: int,
    plan_update: SevkiyatPlaniGuncelleRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: SevkiyatPlaniGuncelleUseCase = Depends(get_sevkiyat_guncelle_uc),
):
    """Sevkiyat planını günceller. Durum makinesi doğrulaması uygulanır."""
    return uc.execute(plan_id, plan_update, kullanici_id=current_user.id)


@router.delete("/{plan_id}")
def sevkiyat_plani_sil(
    plan_id: int,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: SevkiyatPlaniSilUseCase = Depends(get_sevkiyat_sil_uc),
):
    """Sevkiyat planını siler. Teslim edilmiş planlar silinemez."""
    uc.execute(plan_id, kullanici_id=current_user.id)
    return {"success": True, "message": "Sevkiyat planı başarıyla silindi", "id": plan_id}
