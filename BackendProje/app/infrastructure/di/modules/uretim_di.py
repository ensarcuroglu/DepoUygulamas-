"""DI — Üretim Paleti (FAZ 3: Servis Katmanı)."""

from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from app.infrastructure.persistence.repositories.sa_uretim_seri_sayac_repository import (
    SqlAlchemyUretimSeriSayacRepository,
)
from app.infrastructure.persistence.repositories.sa_palet_durum_log_repository import (
    SqlAlchemyPaletDurumLogRepository,
)
from app.infrastructure.services.sql_uretim_seri_no_uretici import SqlUretimSeriNoUretici
from app.core.services.uretim_palet_service import UretimPaletService
from app.application.use_cases.uretim_paleti_use_cases import (
    UretimPaletiOlusturUseCase,
    UretimPaletiKabulBekleUseCase,
    UretimPaletiKabulEtUseCase,
    UretimPaletiKarantinaAlUseCase,
    UretimPaletiKarantinaCikarUseCase,
    UretimPaletiIptalUseCase,
    UretimPaletiYerlestirmeBekleUseCase,
    UretimPaletiYerlestirUseCase,
    UretimPaletleriListeleUseCase,
    UretimPaletiGetirUseCase,
)
from app.infrastructure.di.modules.kullanici_destek_di import get_log_repo
from app.infrastructure.di.modules.depo_envanter_di import (
    get_palet_repo,
    get_lot_repo,
    get_raf_repo,
    get_hareket_repo,
    get_kapasite_dogrulama_servisi,
)


# ── Repository factory'leri ──

def get_uretim_seri_sayac_repo(db: Session = Depends(get_db)):
    return SqlAlchemyUretimSeriSayacRepository(db)


def get_palet_durum_log_repo(db: Session = Depends(get_db)):
    return SqlAlchemyPaletDurumLogRepository(db)


# ── Servis factory'leri ──

def get_uretim_seri_no_uretici(
    sayac_repo=Depends(get_uretim_seri_sayac_repo),
):
    return SqlUretimSeriNoUretici(sayac_repo)


def get_uretim_palet_service() -> UretimPaletService:
    return UretimPaletService()


# ── Use Case factory'leri ──

def get_uretim_paleti_olustur_uc(
    db: Session = Depends(get_db),
    palet_repo=Depends(get_palet_repo),
    lot_repo=Depends(get_lot_repo),
    raf_repo=Depends(get_raf_repo),
    durum_log_repo=Depends(get_palet_durum_log_repo),
    log_repo=Depends(get_log_repo),
    seri_uretici=Depends(get_uretim_seri_no_uretici),
    domain_svc=Depends(get_uretim_palet_service),
):
    return UretimPaletiOlusturUseCase(
        domain_service=domain_svc,
        seri_no_uretici=seri_uretici,
        palet_repo=palet_repo,
        lot_repo=lot_repo,
        raf_repo=raf_repo,
        durum_log_repo=durum_log_repo,
        sistem_log_repo=log_repo,
        db=db,
    )


def get_uretim_paleti_kabul_bekle_uc(
    db: Session = Depends(get_db),
    palet_repo=Depends(get_palet_repo),
    durum_log_repo=Depends(get_palet_durum_log_repo),
    log_repo=Depends(get_log_repo),
    domain_svc=Depends(get_uretim_palet_service),
):
    return UretimPaletiKabulBekleUseCase(
        domain_service=domain_svc,
        palet_repo=palet_repo,
        durum_log_repo=durum_log_repo,
        sistem_log_repo=log_repo,
        db=db,
    )


def get_uretim_paleti_kabul_et_uc(
    db: Session = Depends(get_db),
    palet_repo=Depends(get_palet_repo),
    lot_repo=Depends(get_lot_repo),
    hareket_repo=Depends(get_hareket_repo),
    durum_log_repo=Depends(get_palet_durum_log_repo),
    log_repo=Depends(get_log_repo),
    domain_svc=Depends(get_uretim_palet_service),
):
    return UretimPaletiKabulEtUseCase(
        domain_service=domain_svc,
        palet_repo=palet_repo,
        lot_repo=lot_repo,
        hareket_repo=hareket_repo,
        durum_log_repo=durum_log_repo,
        sistem_log_repo=log_repo,
        db=db,
    )


def get_uretim_paleti_karantina_al_uc(
    db: Session = Depends(get_db),
    palet_repo=Depends(get_palet_repo),
    durum_log_repo=Depends(get_palet_durum_log_repo),
    log_repo=Depends(get_log_repo),
    domain_svc=Depends(get_uretim_palet_service),
):
    return UretimPaletiKarantinaAlUseCase(
        domain_service=domain_svc,
        palet_repo=palet_repo,
        durum_log_repo=durum_log_repo,
        sistem_log_repo=log_repo,
        db=db,
    )


def get_uretim_paleti_karantina_cikar_uc(
    db: Session = Depends(get_db),
    palet_repo=Depends(get_palet_repo),
    durum_log_repo=Depends(get_palet_durum_log_repo),
    log_repo=Depends(get_log_repo),
    domain_svc=Depends(get_uretim_palet_service),
):
    return UretimPaletiKarantinaCikarUseCase(
        domain_service=domain_svc,
        palet_repo=palet_repo,
        durum_log_repo=durum_log_repo,
        sistem_log_repo=log_repo,
        db=db,
    )


def get_uretim_paleti_iptal_uc(
    db: Session = Depends(get_db),
    palet_repo=Depends(get_palet_repo),
    durum_log_repo=Depends(get_palet_durum_log_repo),
    log_repo=Depends(get_log_repo),
    domain_svc=Depends(get_uretim_palet_service),
):
    return UretimPaletiIptalUseCase(
        domain_service=domain_svc,
        palet_repo=palet_repo,
        durum_log_repo=durum_log_repo,
        sistem_log_repo=log_repo,
        db=db,
    )


def get_uretim_paleti_yerlestirme_bekle_uc(
    db: Session = Depends(get_db),
    palet_repo=Depends(get_palet_repo),
    durum_log_repo=Depends(get_palet_durum_log_repo),
    log_repo=Depends(get_log_repo),
    domain_svc=Depends(get_uretim_palet_service),
):
    return UretimPaletiYerlestirmeBekleUseCase(
        domain_service=domain_svc,
        palet_repo=palet_repo,
        durum_log_repo=durum_log_repo,
        sistem_log_repo=log_repo,
        db=db,
    )


def get_uretim_paleti_yerlestir_uc(
    db: Session = Depends(get_db),
    palet_repo=Depends(get_palet_repo),
    raf_repo=Depends(get_raf_repo),
    kapasite=Depends(get_kapasite_dogrulama_servisi),
    durum_log_repo=Depends(get_palet_durum_log_repo),
    log_repo=Depends(get_log_repo),
    domain_svc=Depends(get_uretim_palet_service),
):
    return UretimPaletiYerlestirUseCase(
        domain_service=domain_svc,
        palet_repo=palet_repo,
        raf_repo=raf_repo,
        kapasite_servisi=kapasite,
        durum_log_repo=durum_log_repo,
        sistem_log_repo=log_repo,
        db=db,
    )


def get_uretim_paletleri_listele_uc(palet_repo=Depends(get_palet_repo)):
    return UretimPaletleriListeleUseCase(palet_repo=palet_repo)


def get_uretim_paleti_getir_uc(palet_repo=Depends(get_palet_repo)):
    return UretimPaletiGetirUseCase(palet_repo=palet_repo)
