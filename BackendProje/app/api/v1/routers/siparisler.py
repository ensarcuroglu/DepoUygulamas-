"""
Sipariş API Router — Clean Architecture (Thin Controller).

KURAL 1: Router ORM/Session ile doğrudan konuşmaz.
KURAL 2: Tüm iş mantığı DI ile enjekte edilen Use Case üzerinden çalışır.
KURAL 3: İstekler RequestDTO, yanıtlar ResponseDTO ile alınır/döner.
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional, List

from auth import require_role
from models import Kullanici

# ── DI Use Case factory'leri ──
from app.infrastructure.di.container import (
    get_siparis_listele_uc,
    get_siparis_getir_uc,
    get_siparis_olustur_uc,
    get_siparis_guncelle_uc,
    get_siparis_sil_uc,
)

# ── DTO'lar ──
from app.application.dto import (
    SiparisOlusturRequestDTO,
    SiparisGuncelleRequestDTO,
    SiparisResponseDTO,
    SiparisDetayResponseDTO,
)

# ── Use Case tipleri (tip tanımları için) ──
from app.application.use_cases import (
    SiparisListeleUseCase,
    SiparisGetirUseCase,
    SiparisOlusturUseCase,
    SiparisGuncelleUseCase,
    SiparisSilUseCase,
)

router = APIRouter(prefix="/api/siparisler", tags=["Siparişler"])


@router.get("/", response_model=List[SiparisResponseDTO])
def siparisler_listele(
    skip: int = 0,
    limit: int = 100,
    durum: Optional[str] = Query(None),
    arama: Optional[str] = Query(None),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: SiparisListeleUseCase = Depends(get_siparis_listele_uc),
):
    """Sipariş listesini döner. Durum ve arama filtresi destekler."""
    return uc.execute(skip=skip, limit=limit, durum=durum, arama=arama)


@router.get("/{siparis_id}", response_model=SiparisDetayResponseDTO)
def siparis_detay(
    siparis_id: int,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: SiparisGetirUseCase = Depends(get_siparis_getir_uc),
):
    """Tek sipariş detay bilgisini kalemlerle birlikte döner."""
    return uc.execute(siparis_id)


@router.post("/", response_model=SiparisDetayResponseDTO, status_code=201)
def siparis_ekle(
    siparis: SiparisOlusturRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: SiparisOlusturUseCase = Depends(get_siparis_olustur_uc),
):
    """Yeni sipariş oluşturur. Otomatik sipariş numarası atanır."""
    return uc.execute(siparis, kullanici_id=current_user.id)


@router.put("/{siparis_id}", response_model=SiparisDetayResponseDTO)
def siparis_guncelle(
    siparis_id: int,
    siparis_update: SiparisGuncelleRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: SiparisGuncelleUseCase = Depends(get_siparis_guncelle_uc),
):
    """Sipariş bilgilerini ve durumunu günceller. Durum makinesi doğrulaması uygulanır."""
    return uc.execute(siparis_id, siparis_update, kullanici_id=current_user.id)


@router.delete("/{siparis_id}")
def siparis_sil(
    siparis_id: int,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: SiparisSilUseCase = Depends(get_siparis_sil_uc),
):
    """Siparişi pasife alır (soft delete). Teslim edilmiş siparişler silinemez."""
    uc.execute(siparis_id, kullanici_id=current_user.id)
    return {"success": True, "message": "Sipariş başarıyla pasife alındı", "id": siparis_id}
