"""
Toplama Görevi API Router — Clean Architecture (Thin Controller).
"""

from fastapi import APIRouter, Depends, Header, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.auth import require_role
from app.core.idempotency import idempotency_kontrol, idempotency_kaydet
from database import get_db
from app.core.exceptions import GecersizIslemError, YetkisizIslemError
from models import Kullanici

from app.infrastructure.di.container import (
    get_toplama_gorevi_listele_uc,
    get_toplama_gorevi_getir_uc,
    get_pick_task_uret_uc,
    get_siradan_gorev_al_uc,
    get_gorev_baslat_uc,
    get_gorev_tamamla_uc,
    get_gorev_iptal_uc,
    get_fefo_override_uc,
)
from app.application.dto.toplama_gorevi_dto import (
    ToplamaGoreviResponseDTO,
    PickTaskUretRequestDTO,
    SiradanGorevAlRequestDTO,
    GorevIptalRequestDTO,
    FefoOverrideRequestDTO,
)
from app.application.use_cases.toplama_gorevi_use_cases import (
    ToplamaGoreviListeleUseCase,
    ToplamaGoreviGetirUseCase,
    PickTaskUretUseCase,
    SiradanGorevAlUseCase,
    GorevBaslatUseCase,
    GorevTamamlaUseCase,
    GorevIptalUseCase,
    FefoOverrideUseCase,
)

router = APIRouter(prefix="/api/v1/toplama-gorevleri", tags=["Toplama Görevleri"])


def _depocu_depo_id(current_user: Kullanici) -> Optional[int]:
    if current_user.rol != "depocu":
        return None
    if getattr(current_user, "depo_erisimi_yok", False):
        raise GecersizIslemError(
            "Bu kullanicinin hicbir depoda yetkisi yok. Lutfen yoneticiniz ile iletisime gecin."
        )
    if current_user.depo_id is None:
        raise GecersizIslemError(
            "Depocu kullanicisina depo atanmamis. Lutfen yoneticiniz ile iletisime gecin."
        )
    return current_user.depo_id


def _gorev_depo_yetkisini_dogrula(
    gorev: ToplamaGoreviResponseDTO,
    current_user: Kullanici,
) -> None:
    depocu_depo_id = _depocu_depo_id(current_user)
    if depocu_depo_id is None:
        return
    if gorev.depo_id is not None and gorev.depo_id != depocu_depo_id:
        raise YetkisizIslemError("Bu gorev farkli bir depoya ait, erisim yetkiniz bulunmuyor.")


@router.get("/", response_model=List[ToplamaGoreviResponseDTO])
def gorev_listele(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    durum: Optional[str] = Query(None),
    depo_id: Optional[int] = Query(None),
    kullanici_id: Optional[int] = Query(None),
    sevkiyat_id: Optional[int] = Query(None),
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    uc: ToplamaGoreviListeleUseCase = Depends(get_toplama_gorevi_listele_uc),
):
    hedef_depo_id = _depocu_depo_id(current_user)
    if hedef_depo_id is None:
        hedef_depo_id = depo_id

    return uc.execute(
        skip=skip,
        limit=limit,
        durum=durum,
        depo_id=hedef_depo_id,
        kullanici_id=kullanici_id,
        sevkiyat_id=sevkiyat_id,
    )


@router.get("/{gorev_id}", response_model=ToplamaGoreviResponseDTO)
def gorev_getir(
    gorev_id: int,
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    uc: ToplamaGoreviGetirUseCase = Depends(get_toplama_gorevi_getir_uc),
):
    gorev = uc.execute(gorev_id)
    _gorev_depo_yetkisini_dogrula(gorev, current_user)
    return gorev


@router.post("/uret", response_model=List[ToplamaGoreviResponseDTO], status_code=201)
def gorev_uret(
    dto: PickTaskUretRequestDTO,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: PickTaskUretUseCase = Depends(get_pick_task_uret_uc),
    db: Session = Depends(get_db),
):
    """Sevkiyat için palet bazlı toplama görevlerini üretir."""
    if idempotency_key:
        cached = idempotency_kontrol(db, idempotency_key, "gorev_uret")
        if cached is not None:
            return cached

    sonuc = uc.execute(dto.sevkiyat_id, current_user.id)

    if idempotency_key:
        idempotency_kaydet(db, idempotency_key, "gorev_uret",
                           [r.model_dump(mode="json") for r in sonuc])
    return sonuc


@router.post("/sira-al", response_model=Optional[ToplamaGoreviResponseDTO])
def siradan_gorev_al(
    dto: SiradanGorevAlRequestDTO,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    uc: SiradanGorevAlUseCase = Depends(get_siradan_gorev_al_uc),
    db: Session = Depends(get_db),
):
    """Operatör sıradaki Beklemede görevi havuzdan çeker (pull-based)."""
    if idempotency_key:
        cached = idempotency_kontrol(db, idempotency_key, "siradan_gorev_al")
        if cached is not None:
            return cached

    hedef_depo_id = _depocu_depo_id(current_user)
    if hedef_depo_id is None:
        hedef_depo_id = dto.depo_id
    sonuc = uc.execute(kullanici_id=current_user.id, depo_id=hedef_depo_id)

    # None yanıtı (görev yok) cache'lenmez — retry yeni görev bulabilmeli
    if idempotency_key and sonuc is not None:
        idempotency_kaydet(db, idempotency_key, "siradan_gorev_al",
                           sonuc.model_dump(mode="json"))
    return sonuc


@router.post("/{gorev_id}/baslat", response_model=ToplamaGoreviResponseDTO)
def gorev_baslat(
    gorev_id: int,
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    uc: GorevBaslatUseCase = Depends(get_gorev_baslat_uc),
):
    return uc.execute(gorev_id, current_user.id)


@router.post("/{gorev_id}/tamamla", response_model=ToplamaGoreviResponseDTO)
def gorev_tamamla(
    gorev_id: int,
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    uc: GorevTamamlaUseCase = Depends(get_gorev_tamamla_uc),
):
    return uc.execute(gorev_id, current_user.id)


@router.post("/{gorev_id}/iptal", response_model=ToplamaGoreviResponseDTO)
def gorev_iptal(
    gorev_id: int,
    dto: GorevIptalRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "depocu", "lojistik")),
    uc: GorevIptalUseCase = Depends(get_gorev_iptal_uc),
):
    return uc.execute(gorev_id, current_user.id, neden=dto.neden)


@router.post("/{gorev_id}/fefo-override", response_model=ToplamaGoreviResponseDTO)
def fefo_override(
    gorev_id: int,
    dto: FefoOverrideRequestDTO,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: FefoOverrideUseCase = Depends(get_fefo_override_uc),
):
    """Admin FEFO override — göreve farklı palet atar (audit log yazılır)."""
    return uc.execute(gorev_id, dto, current_user.id, current_user.rol)
