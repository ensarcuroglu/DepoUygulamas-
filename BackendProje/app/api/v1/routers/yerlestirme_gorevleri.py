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
)
from app.application.dto.yerlestirme_gorevi_dto import (
    YerlestirmeGoreviOlusturRequestDTO,
    YerlestirmeGoreviTamamlaRequestDTO,
    YerlestirmeGoreviOverrideRequestDTO,
    YerlestirmeGoreviIptalRequestDTO,
    YerlestirmeGoreviResponseDTO,
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


@router.post("/sonraki-gorevi-al", response_model=Optional[YerlestirmeGoreviResponseDTO])
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
