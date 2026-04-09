from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from datetime import datetime, date

from app.core.auth import require_role
from models import Kullanici

from app.infrastructure.di.container import (
    get_mal_kabul_irsaliye_listele_uc,
    get_mal_kabul_irsaliye_getir_uc,
    get_mal_kabul_irsaliye_olustur_uc,
    get_mal_kabul_irsaliye_guncelle_uc,
    get_mal_kabul_irsaliye_sil_uc,
    get_irsaliye_onayla_ve_gorev_olustur_uc,
    get_mal_kabul_kalemi_istisna_bildir_uc,
    get_inbound_dashboard_uc,
    get_inbound_kpi_uc,
)

from app.application.dto import (
    MalKabulIrsaliyeOlusturRequestDTO,
    MalKabulIrsaliyeGuncelleRequestDTO,
    MalKabulIrsaliyeResponseDTO,
    MalKabulKalemiIstisnaRequestDTO,
    InboundDashboardResponseDTO,
    InboundKpiResponseDTO,
)

from app.application.use_cases import (
    MalKabulIrsaliyeListeleUseCase,
    MalKabulIrsaliyeGetirUseCase,
    MalKabulIrsaliyeOlusturUseCase,
    MalKabulIrsaliyeGuncelleUseCase,
    MalKabulIrsaliyeSilUseCase,
    IrsaliyeOnaylaVeGorevOlusturUseCase,
    MalKabulKalemiIstisnaBildirUseCase,
    InboundDashboardUseCase,
    InboundKpiUseCase,
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


@router.get("/inbound-dashboard", response_model=InboundDashboardResponseDTO)
def inbound_dashboard(
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: InboundDashboardUseCase = Depends(get_inbound_dashboard_uc),
):
    """Inbound kontrol paneli — bugünkü operasyon özeti."""
    return uc.execute()


@router.get("/kpi", response_model=InboundKpiResponseDTO)
def inbound_kpi(
    tarih_baslangic: Optional[date] = Query(
        None,
        description="ISO format (YYYY-MM-DD). Varsayılan: bugün 00:00",
    ),
    tarih_bitis: Optional[date] = Query(
        None,
        description="ISO format (YYYY-MM-DD). Varsayılan: bugün 23:59",
    ),
    staging_esik_saat: int = Query(
        default=24,
        ge=1,
        le=720,
        description="Staging uyarı eşiği (saat). Varsayılan: 24",
    ),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: InboundKpiUseCase = Depends(get_inbound_kpi_uc),
):
    """Inbound operasyon KPI metrikleri — tarih aralığı ve staging eşiğine göre."""
    bugun = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    if tarih_baslangic:
        bas = datetime.combine(tarih_baslangic, datetime.min.time()).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    else:
        bas = bugun

    if tarih_bitis:
        bitis = datetime.combine(tarih_bitis, datetime.max.time()).replace(
            hour=23, minute=59, second=59, microsecond=0
        )
    else:
        bitis = bugun.replace(hour=23, minute=59, second=59)

    return uc.execute(
        tarih_baslangic=bas,
        tarih_bitis=bitis,
        staging_esik_saat=staging_esik_saat,
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


@router.put("/{irsaliye_id}/kalemler/{kalem_id}/istisna", response_model=MalKabulIrsaliyeResponseDTO)
def mal_kabul_kalemi_istisna_bildir(
    irsaliye_id: int,
    kalem_id: int,
    istisna: MalKabulKalemiIstisnaRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "depocu")),
    uc: MalKabulKalemiIstisnaBildirUseCase = Depends(get_mal_kabul_kalemi_istisna_bildir_uc),
):
    """Mal kabul kalemi için fark/hasar/istisna kaydeder."""
    return uc.execute(irsaliye_id, kalem_id, istisna, kullanici_id=current_user.id)
