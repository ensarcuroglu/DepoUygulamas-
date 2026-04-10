"""
Sistem Log Use Case'leri.

Salt okunur modül — sadece listeleme ve frontend'den log oluşturma.
"""

from __future__ import annotations
from typing import List

from app.core.repositories.sistem_log_repository import ISistemLogRepository
from app.core.entities.sistem_log import SistemLog
from app.application.dto.sistem_log_dto import (
    SistemLogOlusturRequestDTO,
    SistemLogResponseDTO,
)


class SistemLogListeleUseCase:
    def __init__(self, log_repo: ISistemLogRepository):
        self._log_repo = log_repo

    def execute(self, skip: int = 0, limit: int = 100) -> List[SistemLogResponseDTO]:
        limit = min(limit, 1000)
        loglar = self._log_repo.getir_hepsi(skip=skip, limit=limit)
        return [SistemLogResponseDTO.from_entity(log) for log in loglar]


class SistemLogOlusturUseCase:
    """Frontend'den doğrudan log kaydetmek için."""

    def __init__(self, log_repo: ISistemLogRepository):
        self._log_repo = log_repo

    def execute(self, dto: SistemLogOlusturRequestDTO, kullanici_id: int) -> SistemLogResponseDTO:
        log = SistemLog.olustur(
            kullanici_id=kullanici_id,
            islem_tipi=dto.islem_tipi,
            modul=dto.modul,
            detay=dto.detay,
            eski_veri=dto.eski_veri,
            yeni_veri=dto.yeni_veri,
        )
        kaydedilen = self._log_repo.olustur(log)
        return SistemLogResponseDTO.from_entity(kaydedilen)
