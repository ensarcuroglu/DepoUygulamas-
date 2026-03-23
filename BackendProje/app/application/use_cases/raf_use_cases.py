"""
Raf Use Case'leri.
"""

from __future__ import annotations
from typing import List, Optional

from app.core.repositories.raf_repository import IRafRepository
from app.core.repositories.depo_repository import IDepoRepository
from app.core.repositories.sistem_log_repository import ISistemLogRepository
from app.core.entities.raf import Raf
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.exceptions import KayitBulunamadiError, CakismaHatasi
from app.application.dto.raf_dto import (
    RafOlusturRequestDTO,
    RafGuncelleRequestDTO,
    RafResponseDTO,
)


class RafListeleUseCase:
    """Raf listesini döner, depo_id ile filtrelenebilir."""

    def __init__(self, raf_repo: IRafRepository):
        self._raf_repo = raf_repo

    def execute(
        self, skip: int = 0, limit: int = 500, depo_id: Optional[int] = None
    ) -> List[RafResponseDTO]:
        raflar = self._raf_repo.getir_hepsi(skip=skip, limit=limit, depo_id=depo_id)
        return [RafResponseDTO.from_entity(r) for r in raflar]


class RafGetirUseCase:
    """ID ile tek raf getirir."""

    def __init__(self, raf_repo: IRafRepository):
        self._raf_repo = raf_repo

    def execute(self, raf_id: int) -> RafResponseDTO:
        raf = self._raf_repo.getir_id_ile(raf_id)
        if not raf:
            raise KayitBulunamadiError("Raf", raf_id)
        return RafResponseDTO.from_entity(raf)


class RafOlusturUseCase:
    """
    Yeni raf oluşturur.

    İş kuralları:
    - Bağlı depo var olmalı.
    - Aynı depoda mükerrer raf kodu olamaz.
    """

    def __init__(
        self,
        raf_repo: IRafRepository,
        depo_repo: IDepoRepository,
        log_repo: ISistemLogRepository,
    ):
        self._raf_repo = raf_repo
        self._depo_repo = depo_repo
        self._log_repo = log_repo

    def execute(self, dto: RafOlusturRequestDTO, kullanici_id: int) -> RafResponseDTO:
        # Depo varlık kontrolü
        depo = self._depo_repo.getir_id_ile(dto.depo_id)
        if not depo:
            raise KayitBulunamadiError("Depo", dto.depo_id)

        # Aynı depoda mükerrer raf kodu kontrolü (DB seviyesinde tek sorgu)
        mevcut_raf = self._raf_repo.getir_kod_ile(dto.kod, dto.depo_id)
        if mevcut_raf:
            raise CakismaHatasi("Raf kodu", dto.kod)

        raf = Raf(
            depo_id=dto.depo_id,
            kod=dto.kod,
            bolge=dto.bolge,
            kapasite=dto.kapasite,
        )
        kaydedilen = self._raf_repo.olustur(raf)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.CREATE,
                modul="Raf Yönetimi",
                detay=f"Yeni raf eklendi: {kaydedilen.kod} (Depo: {depo.isim})",
                yeni_veri={"kod": kaydedilen.kod, "depo_id": kaydedilen.depo_id},
            )
        )

        return RafResponseDTO.from_entity(kaydedilen)


class RafGuncelleUseCase:
    """Mevcut rafı günceller."""

    def __init__(self, raf_repo: IRafRepository, log_repo: ISistemLogRepository):
        self._raf_repo = raf_repo
        self._log_repo = log_repo

    def execute(
        self, raf_id: int, dto: RafGuncelleRequestDTO, kullanici_id: int
    ) -> RafResponseDTO:
        mevcut = self._raf_repo.getir_id_ile(raf_id)
        if not mevcut:
            raise KayitBulunamadiError("Raf", raf_id)

        eski_veri = {"kod": mevcut.kod, "kapasite": mevcut.kapasite}

        # Kod değişiyorsa çakışma kontrolü
        guncel_veri = dto.model_dump(exclude_unset=True)
        yeni_kod = guncel_veri.get("kod")
        hedef_depo = guncel_veri.get("depo_id", mevcut.depo_id)
        if yeni_kod and (yeni_kod.lower() != mevcut.kod.lower() or hedef_depo != mevcut.depo_id):
            sahip = self._raf_repo.getir_kod_ile(yeni_kod, hedef_depo)
            if sahip and sahip.id != raf_id:
                raise CakismaHatasi("Raf kodu", yeni_kod)

        for alan, deger in guncel_veri.items():
            setattr(mevcut, alan, deger)

        kaydedilen = self._raf_repo.guncelle(mevcut)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Raf Yönetimi",
                detay=f"Raf güncellendi: {kaydedilen.kod}",
                eski_veri=eski_veri,
                yeni_veri={"kod": kaydedilen.kod, "kapasite": kaydedilen.kapasite},
            )
        )

        return RafResponseDTO.from_entity(kaydedilen)


class RafSilUseCase:
    """Rafı pasife alır (soft delete)."""

    def __init__(self, raf_repo: IRafRepository, log_repo: ISistemLogRepository):
        self._raf_repo = raf_repo
        self._log_repo = log_repo

    def execute(self, raf_id: int, kullanici_id: int) -> None:
        raf = self._raf_repo.getir_id_ile(raf_id)
        if not raf:
            raise KayitBulunamadiError("Raf", raf_id)

        self._raf_repo.sil(raf_id)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.DELETE,
                modul="Raf Yönetimi",
                detay=f"Raf pasife alındı: {raf.kod} (ID: {raf_id})",
            )
        )
