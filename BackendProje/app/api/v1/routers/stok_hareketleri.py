"""
Stok Hareketi API Router — Clean Architecture (Thin Controller).

KURAL 1: Router ORM/Session ile doğrudan konuşmaz.
KURAL 2: Tüm iş mantığı DI ile enjekte edilen Use Case üzerinden çalışır.
KURAL 3: İstekler RequestDTO, yanıtlar ResponseDTO ile alınır/döner.
"""

from fastapi import APIRouter, Depends, Query, Request
from typing import Optional, List

from auth import get_current_user
from models import Kullanici
from limiter import limiter

# ── DI Use Case factory'leri ──
from app.infrastructure.di.container import (
    get_stok_hareketi_listele_uc,
    get_stok_hareketi_olustur_uc,
)

# ── DTO'lar ──
from app.application.dto import (
    StokHareketiOlusturRequestDTO,
    StokHareketiResponseDTO,
)

# ── Use Case tipleri (tip tanımları için) ──
from app.application.use_cases import (
    StokHareketiListeleUseCase,
    StokHareketiOlusturUseCase,
)

router = APIRouter(prefix="/api/stok-hareketleri", tags=["Stok Hareketleri"])


@router.get("/", response_model=List[StokHareketiResponseDTO])
@limiter.limit("100/minute")
def hareketleri_listele(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    urun_id: Optional[int] = Query(None, description="Belirli ürüne göre filtrele"),
    lot_id: Optional[int] = Query(None, description="Belirli LOT'a göre filtrele"),
    hareket_tipi: Optional[str] = Query(None, description="'giris' veya 'cikis' olarak filtrele"),
    current_user: Kullanici = Depends(get_current_user),
    uc: StokHareketiListeleUseCase = Depends(get_stok_hareketi_listele_uc),
):
    """Stok hareketlerini listeler. Ürün, LOT veya hareket tipine göre filtreleme destekler."""
    return uc.execute(
        skip=skip, limit=limit,
        urun_id=urun_id, lot_id=lot_id, hareket_tipi=hareket_tipi,
    )


@router.post("/", response_model=StokHareketiResponseDTO, status_code=201)
@limiter.limit("50/minute")
def hareket_ekle(
    request: Request,
    hareket: StokHareketiOlusturRequestDTO,
    current_user: Kullanici = Depends(get_current_user),
    uc: StokHareketiOlusturUseCase = Depends(get_stok_hareketi_olustur_uc),
):
    """
    Yeni stok hareketi oluşturur.
    - hareket_tipi: 'giris' veya 'cikis'
    - Çıkışta FIFO mantığıyla otomatik palet stoğu düşer
    - Girişte otomatik lot ve palet oluşturulur
    """
    return uc.execute(hareket, kullanici_id=current_user.id)
