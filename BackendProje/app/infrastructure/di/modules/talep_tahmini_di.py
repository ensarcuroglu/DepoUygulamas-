"""DI - Talep Tahmini."""

from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from app.application.use_cases import (
    TalepTahminUrunleriListeleUseCase,
    TalepTahminiGetirUseCase,
)
from app.infrastructure.persistence.repositories import SqlAlchemyTalepTahminiRepository


def get_talep_tahmini_repo(db: Session = Depends(get_db)):
    return SqlAlchemyTalepTahminiRepository(db)


def get_talep_tahmin_urunleri_listele_uc(
    repo=Depends(get_talep_tahmini_repo),
):
    return TalepTahminUrunleriListeleUseCase(repo)


def get_talep_tahmini_getir_uc(
    repo=Depends(get_talep_tahmini_repo),
):
    return TalepTahminiGetirUseCase(repo)

