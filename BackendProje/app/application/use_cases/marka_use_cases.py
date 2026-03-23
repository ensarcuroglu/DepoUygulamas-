"""
Marka Use Case'leri.

Her sınıf tek bir iş eylemini temsil eder; bağımlılıklar sadece
core/repositories içindeki soyut arayüzlerden oluşur.
"""

from __future__ import annotations
from typing import List

from app.core.repositories.marka_repository import IMarkaRepository
from app.core.repositories.sistem_log_repository import ISistemLogRepository
from app.core.entities.marka import Marka
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.exceptions import KayitBulunamadiError, CakismaHatasi
from app.application.dto.marka_dto import (
    MarkaOlusturRequestDTO,
    MarkaGuncelleRequestDTO,
    MarkaResponseDTO,
)


class MarkaListeleUseCase:
    """Marka listesini döner."""

    def __init__(self, marka_repo: IMarkaRepository):
        self._marka_repo = marka_repo

    def execute(self, skip: int = 0, limit: int = 100) -> List[MarkaResponseDTO]:
        markalar = self._marka_repo.getir_hepsi(skip=skip, limit=limit)
        return [MarkaResponseDTO.from_entity(m) for m in markalar]


class MarkaGetirUseCase:
    """ID ile tek marka getirir."""

    def __init__(self, marka_repo: IMarkaRepository):
        self._marka_repo = marka_repo

    def execute(self, marka_id: int) -> MarkaResponseDTO:
        marka = self._marka_repo.getir_id_ile(marka_id)
        if not marka:
            raise KayitBulunamadiError("Marka", marka_id)
        return MarkaResponseDTO.from_entity(marka)


class MarkaOlusturUseCase:
    """Yeni marka oluşturur. İsim benzersiz olmalı."""

    def __init__(self, marka_repo: IMarkaRepository, log_repo: ISistemLogRepository):
        self._marka_repo = marka_repo
        self._log_repo = log_repo

    def execute(self, dto: MarkaOlusturRequestDTO, kullanici_id: int) -> MarkaResponseDTO:
        # İsim çakışma kontrolü (DB seviyesinde tek sorgu)
        mevcut = self._marka_repo.getir_isim_ile(dto.isim)
        if mevcut:
            raise CakismaHatasi("Marka adı", dto.isim)

        marka = Marka(isim=dto.isim, aciklama=dto.aciklama)
        kaydedilen = self._marka_repo.olustur(marka)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.CREATE,
                modul="Marka Yönetimi",
                detay=f"Yeni marka eklendi: {kaydedilen.isim}",
                yeni_veri={"isim": kaydedilen.isim},
            )
        )

        return MarkaResponseDTO.from_entity(kaydedilen)


class MarkaGuncelleUseCase:
    """Mevcut markayı günceller."""

    def __init__(self, marka_repo: IMarkaRepository, log_repo: ISistemLogRepository):
        self._marka_repo = marka_repo
        self._log_repo = log_repo

    def execute(
        self, marka_id: int, dto: MarkaGuncelleRequestDTO, kullanici_id: int
    ) -> MarkaResponseDTO:
        mevcut = self._marka_repo.getir_id_ile(marka_id)
        if not mevcut:
            raise KayitBulunamadiError("Marka", marka_id)

        eski_veri = {"isim": mevcut.isim}

        # İsim değişiyorsa çakışma kontrolü
        guncel_veri = dto.model_dump(exclude_unset=True)
        yeni_isim = guncel_veri.get("isim")
        if yeni_isim and yeni_isim.lower() != mevcut.isim.lower():
            sahip = self._marka_repo.getir_isim_ile(yeni_isim)
            if sahip and sahip.id != marka_id:
                raise CakismaHatasi("Marka adı", yeni_isim)

        for alan, deger in guncel_veri.items():
            setattr(mevcut, alan, deger)

        kaydedilen = self._marka_repo.guncelle(mevcut)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Marka Yönetimi",
                detay=f"Marka güncellendi: {kaydedilen.isim}",
                eski_veri=eski_veri,
                yeni_veri={"isim": kaydedilen.isim},
            )
        )

        return MarkaResponseDTO.from_entity(kaydedilen)


class MarkaSilUseCase:
    """Markayı pasife alır (soft delete)."""

    def __init__(self, marka_repo: IMarkaRepository, log_repo: ISistemLogRepository):
        self._marka_repo = marka_repo
        self._log_repo = log_repo

    def execute(self, marka_id: int, kullanici_id: int) -> None:
        marka = self._marka_repo.getir_id_ile(marka_id)
        if not marka:
            raise KayitBulunamadiError("Marka", marka_id)

        self._marka_repo.sil(marka_id)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.DELETE,
                modul="Marka Yönetimi",
                detay=f"Marka pasife alındı: {marka.isim} (ID: {marka_id})",
            )
        )
