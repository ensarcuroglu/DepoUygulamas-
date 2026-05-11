"""DI - Belge taslagi and DocAi integration."""

from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from app.application.use_cases import (
    BelgeTaslagiGetirUseCase,
    BelgeTaslagiListeleUseCase,
    BelgeTaslagiOlusturUseCase,
    BelgeTaslagiOnaylaUseCase,
    BelgeTaslagiReddetUseCase,
)
from app.core.config import get_settings
from app.infrastructure.di.modules.depo_envanter_di import (
    get_depo_repo,
    get_mal_kabul_irsaliye_repo,
)
from app.infrastructure.di.modules.katalog_di import get_tedarikci_repo
from app.infrastructure.di.modules.kullanici_destek_di import get_log_repo
from app.infrastructure.di.modules.urun_di import get_urun_repo
from app.infrastructure.persistence.repositories import SqlAlchemyBelgeTaslagiRepository
from app.infrastructure.services.doc_ai_client import DocAiClient


def get_belge_taslagi_repo(db: Session = Depends(get_db)):
    return SqlAlchemyBelgeTaslagiRepository(db)


def get_belge_taslagi_listele_uc(
    repo=Depends(get_belge_taslagi_repo),
):
    return BelgeTaslagiListeleUseCase(repo)


def get_belge_taslagi_getir_uc(
    repo=Depends(get_belge_taslagi_repo),
):
    return BelgeTaslagiGetirUseCase(repo)


def get_belge_taslagi_olustur_uc(
    db: Session = Depends(get_db),
    repo=Depends(get_belge_taslagi_repo),
    depo_repo=Depends(get_depo_repo),
    log_repo=Depends(get_log_repo),
):
    return BelgeTaslagiOlusturUseCase(repo, depo_repo, log_repo, db)


def get_belge_taslagi_onayla_uc(
    db: Session = Depends(get_db),
    taslak_repo=Depends(get_belge_taslagi_repo),
    mal_kabul_repo=Depends(get_mal_kabul_irsaliye_repo),
    tedarikci_repo=Depends(get_tedarikci_repo),
    depo_repo=Depends(get_depo_repo),
    urun_repo=Depends(get_urun_repo),
    log_repo=Depends(get_log_repo),
):
    return BelgeTaslagiOnaylaUseCase(
        taslak_repo,
        mal_kabul_repo,
        tedarikci_repo,
        depo_repo,
        urun_repo,
        log_repo,
        db,
    )


def get_belge_taslagi_reddet_uc(
    db: Session = Depends(get_db),
    repo=Depends(get_belge_taslagi_repo),
    log_repo=Depends(get_log_repo),
):
    return BelgeTaslagiReddetUseCase(repo, log_repo, db)


def get_doc_ai_client():
    return DocAiClient(get_settings())
