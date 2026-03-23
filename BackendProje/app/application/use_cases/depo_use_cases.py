"""
Depo Use Case'leri.
"""

from __future__ import annotations
from typing import List

from app.core.repositories.depo_repository import IDepoRepository
from app.core.repositories.sistem_log_repository import ISistemLogRepository
from app.core.entities.depo import Depo
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.exceptions import KayitBulunamadiError
from app.application.dto.depo_dto import (
    DepoOlusturRequestDTO,
    DepoGuncelleRequestDTO,
    DepoResponseDTO,
)


class DepoListeleUseCase:
    """Depo listesini döner."""

    def __init__(self, depo_repo: IDepoRepository):
        self._depo_repo = depo_repo

    def execute(self, skip: int = 0, limit: int = 100) -> List[DepoResponseDTO]:
        depolar = self._depo_repo.getir_hepsi(skip=skip, limit=limit)
        return [DepoResponseDTO.from_entity(d) for d in depolar]


class DepoGetirUseCase:
    """ID ile tek depo getirir."""

    def __init__(self, depo_repo: IDepoRepository):
        self._depo_repo = depo_repo

    def execute(self, depo_id: int) -> DepoResponseDTO:
        depo = self._depo_repo.getir_id_ile(depo_id)
        if not depo:
            raise KayitBulunamadiError("Depo", depo_id)
        return DepoResponseDTO.from_entity(depo)


class DepoOlusturUseCase:
    """Yeni depo oluşturur."""

    def __init__(self, depo_repo: IDepoRepository, log_repo: ISistemLogRepository):
        self._depo_repo = depo_repo
        self._log_repo = log_repo

    def execute(self, dto: DepoOlusturRequestDTO, kullanici_id: int) -> DepoResponseDTO:
        depo = Depo(isim=dto.isim, adres=dto.adres, aciklama=dto.aciklama)
        kaydedilen = self._depo_repo.olustur(depo)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.CREATE,
                modul="Depo Yönetimi",
                detay=f"Yeni depo eklendi: {kaydedilen.isim}",
                yeni_veri={"isim": kaydedilen.isim, "adres": kaydedilen.adres},
            )
        )

        return DepoResponseDTO.from_entity(kaydedilen)


class DepoGuncelleUseCase:
    """Mevcut depoyu günceller."""

    def __init__(self, depo_repo: IDepoRepository, log_repo: ISistemLogRepository):
        self._depo_repo = depo_repo
        self._log_repo = log_repo

    def execute(
        self, depo_id: int, dto: DepoGuncelleRequestDTO, kullanici_id: int
    ) -> DepoResponseDTO:
        mevcut = self._depo_repo.getir_id_ile(depo_id)
        if not mevcut:
            raise KayitBulunamadiError("Depo", depo_id)

        eski_veri = {"isim": mevcut.isim, "adres": mevcut.adres}

        guncel_veri = dto.model_dump(exclude_unset=True)
        for alan, deger in guncel_veri.items():
            setattr(mevcut, alan, deger)

        kaydedilen = self._depo_repo.guncelle(mevcut)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Depo Yönetimi",
                detay=f"Depo güncellendi: {kaydedilen.isim}",
                eski_veri=eski_veri,
                yeni_veri={"isim": kaydedilen.isim, "adres": kaydedilen.adres},
            )
        )

        return DepoResponseDTO.from_entity(kaydedilen)


class DepoSilUseCase:
    """Depoyu pasife alır (soft delete)."""

    def __init__(self, depo_repo: IDepoRepository, log_repo: ISistemLogRepository):
        self._depo_repo = depo_repo
        self._log_repo = log_repo

    def execute(self, depo_id: int, kullanici_id: int) -> None:
        depo = self._depo_repo.getir_id_ile(depo_id)
        if not depo:
            raise KayitBulunamadiError("Depo", depo_id)

        self._depo_repo.sil(depo_id)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.DELETE,
                modul="Depo Yönetimi",
                detay=f"Depo pasife alındı: {depo.isim} (ID: {depo_id})",
            )
        )
