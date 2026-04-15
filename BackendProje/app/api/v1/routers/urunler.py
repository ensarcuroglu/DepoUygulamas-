"""
Ürün API Router — Clean Architecture (Thin Controller).

KURAL 1: Router ORM/Session ile doğrudan konuşmaz.
KURAL 2: Tüm iş mantığı DI ile enjekte edilen Use Case üzerinden çalışır.
KURAL 3: İstekler RequestDTO, yanıtlar ResponseDTO ile alınır/döner.
"""

from fastapi import APIRouter, Depends, Query, Request
from typing import Optional, List, Literal

from app.core.auth import get_current_user, require_role
from models import Kullanici
from limiter import limiter

# ── DI Use Case factory'leri ──
from app.infrastructure.di.container import (
    get_urun_listele_uc,
    get_urun_getir_uc,
    get_kritik_urunler_uc,
    get_urun_olustur_uc,
    get_urun_guncelle_uc,
    get_urun_sil_uc,
    get_urun_repo,
    get_stok_detay_uc,
)

# ── DTO'lar ──
from app.application.dto import (
    UrunOlusturRequestDTO,
    UrunGuncelleRequestDTO,
    UrunResponseDTO,
    UrunListResponseDTO,
)

# ── Use Case tipleri (tip tanımları için) ──
from app.application.use_cases import (
    UrunListeleUseCase,
    UrunGetirUseCase,
    KritikUrunleriGetirUseCase,
    UrunOlusturUseCase,
    UrunGuncelleUseCase,
    UrunSilUseCase,
)
from app.core.repositories.urun_repository import IUrunRepository

router = APIRouter(prefix="/api/urunler", tags=["Ürünler"])


@router.get("/", response_model=List[UrunListResponseDTO])
@limiter.limit("100/minute")
def urunleri_listele(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = Query(None, description="İsim, barkod, EAN veya açıklama ile ara"),
    kategori_id: Optional[int] = Query(None, description="Kategoriye göre filtrele"),
    marka_id: Optional[int] = Query(None, description="Markaya göre filtrele"),
    current_user: Kullanici = Depends(get_current_user),
    uc: UrunListeleUseCase = Depends(get_urun_listele_uc),
):
    """Tüm ürünleri listeler. Arama, kategori ve marka filtresi destekler."""
    return uc.execute(
        skip=skip, limit=limit,
        search=search, kategori_id=kategori_id, marka_id=marka_id,
    )


@router.get("/kritik", response_model=List[UrunListResponseDTO])
@limiter.limit("50/minute")
def kritik_urunleri_getir(
    request: Request,
    current_user: Kullanici = Depends(get_current_user),
    uc: KritikUrunleriGetirUseCase = Depends(get_kritik_urunler_uc),
):
    """Min stok seviyesinin altındaki ürünleri getirir."""
    return uc.execute()


@router.get("/barkod/{barkod_kodu}", response_model=UrunResponseDTO)
@limiter.limit("100/minute")
def urun_getir_by_barkod(
    request: Request,
    barkod_kodu: str,
    current_user: Kullanici = Depends(get_current_user),
    uc: UrunGetirUseCase = Depends(get_urun_getir_uc),
):
    """Barkod veya EAN numarasına göre tek bir ürün getirir."""
    return uc.by_barkod(barkod_kodu)


@router.get("/barkod-kontrol")
@limiter.limit("200/minute")
def barkod_kontrol(
    request: Request,
    deger: str = Query(..., description="Kontrol edilecek barkod veya EAN değeri"),
    alan: Literal["barkod", "ean"] = Query(..., description="Hangi alan kontrol edilecek"),
    exclude_id: Optional[int] = Query(None, description="Güncelleme sırasında hariç tutulacak ürün ID'si"),
    current_user: Kullanici = Depends(require_role("admin")),
    urun_repo: IUrunRepository = Depends(get_urun_repo),
):
    """Barkod veya EAN değerinin sistemde kullanılıp kullanılmadığını kontrol eder."""
    if alan == "barkod":
        mevcut = urun_repo.getir_barkod_ile(deger)
    else:
        mevcut = urun_repo.getir_ean_ile(deger)

    if mevcut and mevcut.id != exclude_id:
        return {"musait": False, "mevcut_urun": {"id": mevcut.id, "isim": mevcut.isim}}

    return {"musait": True, "mevcut_urun": None}


@router.get("/{urun_id}", response_model=UrunResponseDTO)
@limiter.limit("100/minute")
def urun_detay(
    request: Request,
    urun_id: int,
    current_user: Kullanici = Depends(get_current_user),
    uc: UrunGetirUseCase = Depends(get_urun_getir_uc),
):
    """Belirli bir ürünün tüm detaylarını getirir."""
    return uc.by_id(urun_id)


@router.post("/", response_model=UrunResponseDTO, status_code=201)
@limiter.limit("50/minute")
def urun_ekle(
    request: Request,
    urun: UrunOlusturRequestDTO,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: UrunOlusturUseCase = Depends(get_urun_olustur_uc),
):
    """Yeni bir ürün ekler. Sadece admin."""
    return uc.execute(urun, kullanici_id=current_user.id)


@router.put("/{urun_id}", response_model=UrunResponseDTO)
@limiter.limit("50/minute")
def urun_guncelle(
    request: Request,
    urun_id: int,
    urun: UrunGuncelleRequestDTO,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: UrunGuncelleUseCase = Depends(get_urun_guncelle_uc),
):
    """Mevcut bir ürünü günceller. Sadece admin."""
    return uc.execute(urun_id, urun, kullanici_id=current_user.id)


@router.delete("/{urun_id}")
@limiter.limit("50/minute")
def urun_sil(
    request: Request,
    urun_id: int,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: UrunSilUseCase = Depends(get_urun_sil_uc),
):
    """Bir ürünü pasife alır (soft delete). Sadece admin."""
    uc.execute(urun_id, kullanici_id=current_user.id)
    return {"success": True, "message": "Ürün başarıyla pasife alındı", "id": urun_id}


@router.get("/{urun_id}/stok-detay")
def urun_stok_detay(
    urun_id: int,
    current_user: Kullanici = Depends(get_current_user),
    uc=Depends(get_stok_detay_uc),
):
    """Ürün bazlı stok görünürlük özeti: toplam / uygun / rezerve."""
    from app.application.use_cases.palet_rezervasyonu_use_cases import StokDetayUseCase
    return uc.execute(urun_id)
