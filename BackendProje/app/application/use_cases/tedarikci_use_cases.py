"""
Tedarikçi Use Case'leri.
"""

from __future__ import annotations
from typing import List

from app.core.repositories.tedarikci_repository import ITedarikciRepository
from app.core.repositories.sistem_log_repository import ISistemLogRepository
from app.core.entities.tedarikci import Tedarikci
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.exceptions import KayitBulunamadiError
from app.application.dto.tedarikci_dto import (
    TedarikciOlusturRequestDTO,
    TedarikciGuncelleRequestDTO,
    TedarikciResponseDTO,
)


class TedarikciListeleUseCase:
    """Tedarikçi listesini döner."""

    def __init__(self, tedarikci_repo: ITedarikciRepository):
        self._tedarikci_repo = tedarikci_repo

    def execute(self, skip: int = 0, limit: int = 100) -> List[TedarikciResponseDTO]:
        tedarikciler = self._tedarikci_repo.getir_hepsi(skip=skip, limit=limit)
        return [TedarikciResponseDTO.from_entity(t) for t in tedarikciler]


class TedarikciGetirUseCase:
    """ID ile tek tedarikçi getirir."""

    def __init__(self, tedarikci_repo: ITedarikciRepository):
        self._tedarikci_repo = tedarikci_repo

    def execute(self, tedarikci_id: int) -> TedarikciResponseDTO:
        tedarikci = self._tedarikci_repo.getir_id_ile(tedarikci_id)
        if not tedarikci:
            raise KayitBulunamadiError("Tedarikçi", tedarikci_id)
        return TedarikciResponseDTO.from_entity(tedarikci)


class TedarikciOlusturUseCase:
    """Yeni tedarikçi oluşturur."""

    def __init__(self, tedarikci_repo: ITedarikciRepository, log_repo: ISistemLogRepository):
        self._tedarikci_repo = tedarikci_repo
        self._log_repo = log_repo

    def execute(self, dto: TedarikciOlusturRequestDTO, kullanici_id: int) -> TedarikciResponseDTO:
        tedarikci = Tedarikci(
            firma_adi=dto.firma_adi,
            iletisim_kisi=dto.iletisim_kisi,
            telefon=dto.telefon,
            email=dto.email,
            adres=dto.adres,
            vergi_no=dto.vergi_no,
        )
        kaydedilen = self._tedarikci_repo.olustur(tedarikci)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.CREATE,
                modul="Tedarikçi Yönetimi",
                detay=f"Yeni tedarikçi eklendi: {kaydedilen.firma_adi}",
                yeni_veri={"firma_adi": kaydedilen.firma_adi},
            )
        )

        return TedarikciResponseDTO.from_entity(kaydedilen)


class TedarikciGuncelleUseCase:
    """Mevcut tedarikçiyi günceller."""

    def __init__(self, tedarikci_repo: ITedarikciRepository, log_repo: ISistemLogRepository):
        self._tedarikci_repo = tedarikci_repo
        self._log_repo = log_repo

    def execute(
        self, tedarikci_id: int, dto: TedarikciGuncelleRequestDTO, kullanici_id: int
    ) -> TedarikciResponseDTO:
        mevcut = self._tedarikci_repo.getir_id_ile(tedarikci_id)
        if not mevcut:
            raise KayitBulunamadiError("Tedarikçi", tedarikci_id)

        eski_veri = {"firma_adi": mevcut.firma_adi}

        guncel_veri = dto.model_dump(exclude_unset=True)
        for alan, deger in guncel_veri.items():
            setattr(mevcut, alan, deger)

        kaydedilen = self._tedarikci_repo.guncelle(mevcut)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Tedarikçi Yönetimi",
                detay=f"Tedarikçi güncellendi: {kaydedilen.firma_adi}",
                eski_veri=eski_veri,
                yeni_veri={"firma_adi": kaydedilen.firma_adi},
            )
        )

        return TedarikciResponseDTO.from_entity(kaydedilen)


class TedarikciSilUseCase:
    """Tedarikçiyi pasife alır (soft delete)."""

    def __init__(self, tedarikci_repo: ITedarikciRepository, log_repo: ISistemLogRepository):
        self._tedarikci_repo = tedarikci_repo
        self._log_repo = log_repo

    def execute(self, tedarikci_id: int, kullanici_id: int) -> None:
        tedarikci = self._tedarikci_repo.getir_id_ile(tedarikci_id)
        if not tedarikci:
            raise KayitBulunamadiError("Tedarikçi", tedarikci_id)

        self._tedarikci_repo.sil(tedarikci_id)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.DELETE,
                modul="Tedarikçi Yönetimi",
                detay=f"Tedarikçi pasife alındı: {tedarikci.firma_adi} (ID: {tedarikci_id})",
            )
        )
