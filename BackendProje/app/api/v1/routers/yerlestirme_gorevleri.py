"""
Yerleştirme Görevi API Router — Clean Architecture (Thin Controller).
"""

from fastapi import APIRouter, Depends, Query, Request
from typing import List, Optional

from app.core.auth import require_role
from models import Kullanici
from limiter import limiter

from app.infrastructure.di.container import (
    get_yerlestirme_gorevi_listele_uc,
    get_yerlestirme_gorevi_getir_uc,
    get_yerlestirme_gorevi_olustur_uc,
    get_sonraki_gorevini_al_uc,
    get_yerlestirme_gorevi_baslat_uc,
    get_yerlestirme_gorevi_tamamla_uc,
    get_yerlestirme_gorevi_override_uc,
    get_yerlestirme_gorevi_iptal_uc,
    get_yerlestirme_gorevi_birak_uc,
    get_yerlestirme_gorevi_bekleyen_ozet_uc,
    get_karantinadan_cikar_uc,
    get_karantinaya_al_uc,
    get_bilinmeyen_konum_gorevleri_olustur_uc,
)
from app.application.dto.yerlestirme_gorevi_dto import (
    YerlestirmeGoreviOlusturRequestDTO,
    YerlestirmeGoreviTamamlaRequestDTO,
    YerlestirmeGoreviOverrideRequestDTO,
    YerlestirmeGoreviIptalRequestDTO,
    YerlestirmeGoreviResponseDTO,
    KarantinadanCikarRequestDTO,
    KarantinayaAlRequestDTO,
    BilinmeyenKonumGorevleriOlusturSonucDTO,
)
from app.application.use_cases.yerlestirme_gorevi_use_cases import (
    YerlestirmeGoreviListeleUseCase,
    YerlestirmeGoreviGetirUseCase,
    YerlestirmeGoreviOlusturUseCase,
    SonrakiGorevisiniAlUseCase,
    YerlestirmeGoreviBaslatUseCase,
    YerlestirmeGoreviTamamlaUseCase,
    YerlestirmeGoreviOverrideUseCase,
    YerlestirmeGoreviIptalUseCase,
    YerlestirmeGoreviBirakUseCase,
    YerlestirmeGoreviYerlestirmeGoreviBekleyenOzetUseCase,
    KarantinadanCikarUseCase,
    KarantinayaAlUseCase,
    BilinmeyenKonumGorevleriOlusturUseCase,
)

router = APIRouter(prefix="/api/yerlestirme-gorevleri", tags=["Yerleştirme Görevleri"])


@router.get("/", response_model=List[YerlestirmeGoreviResponseDTO])
@limiter.limit("100/minute")
def gorevleri_listele(
    request: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    durum: Optional[str] = None,
    palet_id: Optional[int] = None,
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    uc: YerlestirmeGoreviListeleUseCase = Depends(get_yerlestirme_gorevi_listele_uc),
):
    return uc.execute(skip=skip, limit=limit, durum=durum, palet_id=palet_id)


@router.get("/benim", response_model=List[YerlestirmeGoreviResponseDTO])
@limiter.limit("100/minute")
def benim_gorevlerim(
    request: Request,
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    uc: YerlestirmeGoreviListeleUseCase = Depends(get_yerlestirme_gorevi_listele_uc),
):
    """Oturum açmış kullanıcıya atanmış görevler."""
    return uc.execute(atanan_kullanici_id=current_user.id)


@router.get("/{gorev_id}", response_model=YerlestirmeGoreviResponseDTO)
@limiter.limit("100/minute")
def gorev_detay(
    request: Request,
    gorev_id: int,
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    uc: YerlestirmeGoreviGetirUseCase = Depends(get_yerlestirme_gorevi_getir_uc),
):
    return uc.execute(gorev_id)


@router.post("/", response_model=YerlestirmeGoreviResponseDTO, status_code=201)
@limiter.limit("50/minute")
def gorev_olustur(
    request: Request,
    dto: YerlestirmeGoreviOlusturRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: YerlestirmeGoreviOlusturUseCase = Depends(get_yerlestirme_gorevi_olustur_uc),
):
    return uc.execute(dto, kullanici_id=current_user.id)


@router.post("/siradaki-al", response_model=Optional[YerlestirmeGoreviResponseDTO])
@limiter.limit("60/minute")
def sonraki_gorevi_al(
    request: Request,
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    uc: SonrakiGorevisiniAlUseCase = Depends(get_sonraki_gorevini_al_uc),
):
    """Pull-based FIFO: Sıradaki görevi kilitleyerek çeker."""
    gorev = uc.execute(kullanici_id=current_user.id)
    if not gorev:
        return None
    return gorev


@router.post("/{gorev_id}/baslat", response_model=YerlestirmeGoreviResponseDTO)
@limiter.limit("60/minute")
def gorev_baslat(
    request: Request,
    gorev_id: int,
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    uc: YerlestirmeGoreviBaslatUseCase = Depends(get_yerlestirme_gorevi_baslat_uc),
):
    return uc.execute(gorev_id, kullanici_id=current_user.id)


@router.post("/{gorev_id}/tamamla", response_model=YerlestirmeGoreviResponseDTO)
@limiter.limit("60/minute")
def gorev_tamamla(
    request: Request,
    gorev_id: int,
    dto: YerlestirmeGoreviTamamlaRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    uc: YerlestirmeGoreviTamamlaUseCase = Depends(get_yerlestirme_gorevi_tamamla_uc),
):
    return uc.execute(gorev_id, dto, kullanici_id=current_user.id)


@router.post("/{gorev_id}/override", response_model=YerlestirmeGoreviResponseDTO)
@limiter.limit("30/minute")
def gorev_override(
    request: Request,
    gorev_id: int,
    dto: YerlestirmeGoreviOverrideRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: YerlestirmeGoreviOverrideUseCase = Depends(get_yerlestirme_gorevi_override_uc),
):
    """Süpervizör override: kapasite/zon kuralı ihlali ile tamamlama."""
    return uc.execute(gorev_id, dto, supervisor_id=current_user.id)


@router.post("/{gorev_id}/iptal", response_model=YerlestirmeGoreviResponseDTO)
@limiter.limit("30/minute")
def gorev_iptal(
    request: Request,
    gorev_id: int,
    dto: YerlestirmeGoreviIptalRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: YerlestirmeGoreviIptalUseCase = Depends(get_yerlestirme_gorevi_iptal_uc),
):
    return uc.execute(gorev_id, dto, kullanici_id=current_user.id)


@router.post("/{gorev_id}/birak", response_model=YerlestirmeGoreviResponseDTO)
@limiter.limit("60/minute")
def gorev_birak(
    request: Request,
    gorev_id: int,
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    uc: YerlestirmeGoreviBirakUseCase = Depends(get_yerlestirme_gorevi_birak_uc),
):
    """Operatör görevi havuza iade eder: ATANDI → BEKLIYOR."""
    return uc.execute(gorev_id, kullanici_id=current_user.id)


@router.get("/bekleyen/ozet")
@limiter.limit("100/minute")
def bekleyen_gorev_ozet(
    request: Request,
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    uc: YerlestirmeGoreviYerlestirmeGoreviBekleyenOzetUseCase = Depends(
        get_yerlestirme_gorevi_bekleyen_ozet_uc
    ),
):
    """Bekleyen görev havuzu özeti: toplam sayı ve öncelik dağılımı."""
    return uc.execute()


@router.post("/karantinadan-cikar", response_model=YerlestirmeGoreviResponseDTO, status_code=201)
@limiter.limit("30/minute")
def karantinadan_cikar(
    request: Request,
    dto: KarantinadanCikarRequestDTO,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: KarantinadanCikarUseCase = Depends(get_karantinadan_cikar_uc),
):
    """Admin onayı: Palet karantinadan çıkar → Transfer görevi oluştur."""
    return uc.execute(dto, kullanici_id=current_user.id)


@router.post("/karantinaya-al", response_model=YerlestirmeGoreviResponseDTO, status_code=201)
@limiter.limit("30/minute")
def karantinaya_al(
    request: Request,
    dto: KarantinayaAlRequestDTO,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: KarantinayaAlUseCase = Depends(get_karantinaya_al_uc),
):
    """Admin: Paleti karantinaya al → Transfer görevi oluştur (oncelik=1)."""
    return uc.execute(dto, kullanici_id=current_user.id)


@router.post(
    "/bilinmeyen-konum-gorevleri-olustur",
    response_model=BilinmeyenKonumGorevleriOlusturSonucDTO,
    status_code=201,
)
@limiter.limit("10/minute")
def bilinmeyen_konum_gorevleri_olustur(
    request: Request,
    depo_id: int,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: BilinmeyenKonumGorevleriOlusturUseCase = Depends(
        get_bilinmeyen_konum_gorevleri_olustur_uc
    ),
):
    """MIGRATION_STAGING raftaki paletler için yüksek öncelikli yerleştirme görevi oluşturur."""
    return uc.execute(depo_id=depo_id, kullanici_id=current_user.id)
