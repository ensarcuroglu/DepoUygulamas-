"""
Zon Use Case'leri.
"""

from __future__ import annotations

from typing import List, Optional

from app.application.dto.zon_dto import (
    ZonGuncelleRequestDTO,
    ZonOlusturRequestDTO,
    ZonResponseDTO,
)
from app.core.entities.sistem_log import IslemTipi, SistemLog
from app.core.entities.zon import Zon
from app.core.exceptions import CakismaHatasi, KayitBulunamadiError
from app.core.repositories.depo_repository import IDepoRepository
from app.core.repositories.sistem_log_repository import ISistemLogRepository
from app.core.repositories.zon_repository import IZonRepository


class ZonListeleUseCase:
    """Zon listesini dondurur."""

    def __init__(self, zon_repo: IZonRepository):
        self._zon_repo = zon_repo

    def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        depo_id: Optional[int] = None,
        tip: Optional[str] = None,
    ) -> List[ZonResponseDTO]:
        zonlar = self._zon_repo.getir_hepsi(skip=skip, limit=limit, depo_id=depo_id, tip=tip)
        return [ZonResponseDTO.from_entity(z) for z in zonlar]


class ZonGetirUseCase:
    """ID ile tek zon getirir."""

    def __init__(self, zon_repo: IZonRepository):
        self._zon_repo = zon_repo

    def execute(self, zon_id: int) -> ZonResponseDTO:
        zon = self._zon_repo.getir_id_ile(zon_id)
        if not zon:
            raise KayitBulunamadiError("Zon", zon_id)
        return ZonResponseDTO.from_entity(zon)


class ZonOlusturUseCase:
    """Yeni zon olusturur."""

    def __init__(
        self,
        zon_repo: IZonRepository,
        depo_repo: IDepoRepository,
        log_repo: ISistemLogRepository,
    ):
        self._zon_repo = zon_repo
        self._depo_repo = depo_repo
        self._log_repo = log_repo

    def execute(self, dto: ZonOlusturRequestDTO, kullanici_id: int) -> ZonResponseDTO:
        depo = self._depo_repo.getir_id_ile(dto.depo_id)
        if not depo:
            raise KayitBulunamadiError("Depo", dto.depo_id)

        mevcut = self._zon_repo.getir_kod_ile(dto.kod)
        if mevcut:
            raise CakismaHatasi("Zon kodu", dto.kod)

        zon = Zon(
            depo_id=dto.depo_id,
            isim=dto.isim,
            tip=dto.tip,
            kod=dto.kod,
            aciklama=dto.aciklama,
            sira=dto.sira,
        )
        kaydedilen = self._zon_repo.olustur(zon)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.CREATE,
                modul="Zon Yonetimi",
                detay=f"Yeni zon eklendi: {kaydedilen.kod} ({kaydedilen.isim})",
                yeni_veri={
                    "depo_id": kaydedilen.depo_id,
                    "kod": kaydedilen.kod,
                    "tip": kaydedilen.tip,
                },
            )
        )

        return ZonResponseDTO.from_entity(kaydedilen)


class ZonGuncelleUseCase:
    """Mevcut zonu gunceller."""

    def __init__(
        self,
        zon_repo: IZonRepository,
        depo_repo: IDepoRepository,
        log_repo: ISistemLogRepository,
    ):
        self._zon_repo = zon_repo
        self._depo_repo = depo_repo
        self._log_repo = log_repo

    def execute(self, zon_id: int, dto: ZonGuncelleRequestDTO, kullanici_id: int) -> ZonResponseDTO:
        mevcut = self._zon_repo.getir_id_ile(zon_id)
        if not mevcut:
            raise KayitBulunamadiError("Zon", zon_id)

        guncel_veri = dto.model_dump(exclude_unset=True)
        yeni_depo_id = guncel_veri.get("depo_id")
        if yeni_depo_id is not None:
            depo = self._depo_repo.getir_id_ile(yeni_depo_id)
            if not depo:
                raise KayitBulunamadiError("Depo", yeni_depo_id)

        yeni_kod = guncel_veri.get("kod")
        if yeni_kod and yeni_kod.lower() != mevcut.kod.lower():
            sahip = self._zon_repo.getir_kod_ile(yeni_kod)
            if sahip and sahip.id != zon_id:
                raise CakismaHatasi("Zon kodu", yeni_kod)

        eski_veri = {
            "depo_id": mevcut.depo_id,
            "kod": mevcut.kod,
            "tip": mevcut.tip,
            "isim": mevcut.isim,
        }

        for alan, deger in guncel_veri.items():
            setattr(mevcut, alan, deger)

        kaydedilen = self._zon_repo.guncelle(mevcut)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Zon Yonetimi",
                detay=f"Zon guncellendi: {kaydedilen.kod} ({kaydedilen.isim})",
                eski_veri=eski_veri,
                yeni_veri={
                    "depo_id": kaydedilen.depo_id,
                    "kod": kaydedilen.kod,
                    "tip": kaydedilen.tip,
                    "isim": kaydedilen.isim,
                },
            )
        )

        return ZonResponseDTO.from_entity(kaydedilen)


class ZonSilUseCase:
    """Zonu pasife alir (soft delete)."""

    def __init__(self, zon_repo: IZonRepository, log_repo: ISistemLogRepository):
        self._zon_repo = zon_repo
        self._log_repo = log_repo

    def execute(self, zon_id: int, kullanici_id: int) -> None:
        zon = self._zon_repo.getir_id_ile(zon_id)
        if not zon:
            raise KayitBulunamadiError("Zon", zon_id)

        self._zon_repo.sil(zon_id)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.DELETE,
                modul="Zon Yonetimi",
                detay=f"Zon pasife alindi: {zon.kod} (ID: {zon_id})",
            )
        )

