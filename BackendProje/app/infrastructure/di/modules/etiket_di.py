"""DI — Etiket Şablonu + Palet Etiket modülü."""

from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from app.core.services.etiket_render_service import EtiketRenderService
from app.infrastructure.persistence.repositories.sa_etiket_sablonu_repository import (
    SqlAlchemyEtiketSablonuRepository,
)
from app.infrastructure.persistence.repositories.sa_palet_etiket_repository import (
    SqlAlchemyPaletEtiketRepository,
)
from app.application.use_cases.etiket_sablonu_use_cases import (
    EtiketSablonlariListeleUseCase,
    EtiketSablonuGetirUseCase,
    EtiketSablonuOlusturUseCase,
    EtiketSablonuGuncelleUseCase,
    EtiketSablonuSilUseCase,
)
from app.application.use_cases.palet_etiket_use_cases import (
    PaletEtiketOlusturUseCase,
    PaletEtiketleriListeleUseCase,
    PaletEtiketYazdirUseCase,
)
from app.infrastructure.di.modules.kullanici_destek_di import get_log_repo
from app.infrastructure.di.modules.depo_envanter_di import get_palet_repo


# ── Repository factory'leri ──

def get_etiket_sablonu_repo(db: Session = Depends(get_db)):
    return SqlAlchemyEtiketSablonuRepository(db)


def get_palet_etiket_repo(db: Session = Depends(get_db)):
    return SqlAlchemyPaletEtiketRepository(db)


# ── Servis factory'leri ──

def get_etiket_render_service() -> EtiketRenderService:
    return EtiketRenderService()


# ── Şablon CRUD use case'leri ──

def get_etiket_sablonlari_listele_uc(repo=Depends(get_etiket_sablonu_repo)):
    return EtiketSablonlariListeleUseCase(repo=repo)


def get_etiket_sablonu_getir_uc(repo=Depends(get_etiket_sablonu_repo)):
    return EtiketSablonuGetirUseCase(repo=repo)


def get_etiket_sablonu_olustur_uc(repo=Depends(get_etiket_sablonu_repo)):
    return EtiketSablonuOlusturUseCase(repo=repo)


def get_etiket_sablonu_guncelle_uc(repo=Depends(get_etiket_sablonu_repo)):
    return EtiketSablonuGuncelleUseCase(repo=repo)


def get_etiket_sablonu_sil_uc(repo=Depends(get_etiket_sablonu_repo)):
    return EtiketSablonuSilUseCase(repo=repo)


# ── Palet Etiket use case'leri ──

def get_palet_etiket_olustur_uc(
    db: Session = Depends(get_db),
    palet_repo=Depends(get_palet_repo),
    sablon_repo=Depends(get_etiket_sablonu_repo),
    etiket_repo=Depends(get_palet_etiket_repo),
    render_service=Depends(get_etiket_render_service),
    log_repo=Depends(get_log_repo),
):
    return PaletEtiketOlusturUseCase(
        palet_repo=palet_repo,
        sablon_repo=sablon_repo,
        etiket_repo=etiket_repo,
        render_service=render_service,
        sistem_log_repo=log_repo,
        db=db,
    )


def get_palet_etiketleri_listele_uc(
    palet_repo=Depends(get_palet_repo),
    etiket_repo=Depends(get_palet_etiket_repo),
):
    return PaletEtiketleriListeleUseCase(palet_repo=palet_repo, etiket_repo=etiket_repo)


def get_palet_etiket_yazdir_uc(
    db: Session = Depends(get_db),
    etiket_repo=Depends(get_palet_etiket_repo),
    log_repo=Depends(get_log_repo),
):
    return PaletEtiketYazdirUseCase(
        etiket_repo=etiket_repo, sistem_log_repo=log_repo, db=db,
    )
