"""
Palet Use Case'leri.
"""

from __future__ import annotations
from typing import List

from app.core.repositories.palet_repository import IPaletRepository
from app.core.repositories.lot_repository import ILotRepository
from app.core.repositories.raf_repository import IRafRepository
from app.core.repositories.sistem_log_repository import ISistemLogRepository
from app.core.entities.palet import Palet
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.exceptions import KayitBulunamadiError, CakismaHatasi
from app.application.dto.palet_dto import (
    PaletOlusturRequestDTO,
    PaletGuncelleRequestDTO,
    PaletResponseDTO,
)


class PaletListeleUseCase:
    def __init__(self, palet_repo: IPaletRepository):
        self._palet_repo = palet_repo

    def execute(
        self,
        skip: int = 0,
        limit: int = 50,
        lot_id: int | None = None,
        raf_id: int | None = None,
        ean: str | None = None,
    ) -> List[PaletResponseDTO]:
        paletler = self._palet_repo.getir_hepsi(
            skip=skip, limit=limit, lot_id=lot_id, raf_id=raf_id, ean=ean
        )
        return [PaletResponseDTO.from_entity(p) for p in paletler]


class PaletGetirUseCase:
    def __init__(self, palet_repo: IPaletRepository):
        self._palet_repo = palet_repo

    def execute(self, palet_id: int) -> PaletResponseDTO:
        palet = self._palet_repo.getir_id_ile(palet_id)
        if not palet:
            raise KayitBulunamadiError("Palet", palet_id)
        return PaletResponseDTO.from_entity(palet)


class PaletBarkodIleGetirUseCase:
    def __init__(self, palet_repo: IPaletRepository):
        self._palet_repo = palet_repo

    def execute(self, palet_no: str) -> PaletResponseDTO:
        palet = self._palet_repo.getir_palet_no_ile(palet_no)
        if not palet:
            raise KayitBulunamadiError("Palet barkodu", palet_no)
        return PaletResponseDTO.from_entity(palet)


class PaletSonrakiNumaraUseCase:
    def __init__(self, palet_repo: IPaletRepository):
        self._palet_repo = palet_repo

    def execute(self) -> str:
        return self._palet_repo.sonraki_palet_no()


class PaletOlusturUseCase:
    def __init__(
        self,
        palet_repo: IPaletRepository,
        lot_repo: ILotRepository,
        raf_repo: IRafRepository,
        log_repo: ISistemLogRepository,
    ):
        self._palet_repo = palet_repo
        self._lot_repo = lot_repo
        self._raf_repo = raf_repo
        self._log_repo = log_repo

    def execute(self, dto: PaletOlusturRequestDTO, kullanici_id: int) -> PaletResponseDTO:
        # Lot varlık kontrolü
        lot = self._lot_repo.getir_id_ile(dto.lot_id)
        if not lot:
            raise KayitBulunamadiError("Lot", dto.lot_id)

        # Raf varlık kontrolü
        raf = self._raf_repo.getir_id_ile(dto.raf_id)
        if not raf:
            raise KayitBulunamadiError("Raf", dto.raf_id)

        # Palet no çakışma kontrolü
        mevcut = self._palet_repo.getir_palet_no_ile(dto.palet_no)
        if mevcut:
            raise CakismaHatasi("Palet numarası", dto.palet_no)

        palet = Palet(
            lot_id=dto.lot_id,
            raf_id=dto.raf_id,
            palet_no=dto.palet_no,
            koli_adedi=dto.koli_adedi,
            palet_kg=dto.palet_kg,
            vardiya=dto.vardiya,
        )
        kaydedilen = self._palet_repo.olustur(palet)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.CREATE,
                modul="Palet Yönetimi",
                detay=f"Yeni palet eklendi: {kaydedilen.palet_no}",
                yeni_veri={"palet_no": kaydedilen.palet_no, "lot_id": kaydedilen.lot_id},
            )
        )

        return PaletResponseDTO.from_entity(kaydedilen)


class PaletGuncelleUseCase:
    def __init__(self, palet_repo: IPaletRepository, log_repo: ISistemLogRepository):
        self._palet_repo = palet_repo
        self._log_repo = log_repo

    def execute(
        self, palet_id: int, dto: PaletGuncelleRequestDTO, kullanici_id: int
    ) -> PaletResponseDTO:
        mevcut = self._palet_repo.getir_id_ile(palet_id)
        if not mevcut:
            raise KayitBulunamadiError("Palet", palet_id)

        eski_veri = {"koli_adedi": mevcut.koli_adedi, "aktif": mevcut.aktif}

        guncel = dto.model_dump(exclude_unset=True)
        for alan, deger in guncel.items():
            setattr(mevcut, alan, deger)

        kaydedilen = self._palet_repo.guncelle(mevcut)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Palet Yönetimi",
                detay=f"Palet güncellendi: {kaydedilen.palet_no}",
                eski_veri=eski_veri,
                yeni_veri={"koli_adedi": kaydedilen.koli_adedi, "aktif": kaydedilen.aktif},
            )
        )

        return PaletResponseDTO.from_entity(kaydedilen)


class PaletSilUseCase:
    def __init__(self, palet_repo: IPaletRepository, log_repo: ISistemLogRepository):
        self._palet_repo = palet_repo
        self._log_repo = log_repo

    def execute(self, palet_id: int, kullanici_id: int) -> None:
        palet = self._palet_repo.getir_id_ile(palet_id)
        if not palet:
            raise KayitBulunamadiError("Palet", palet_id)

        self._palet_repo.sil(palet_id)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.DELETE,
                modul="Palet Yönetimi",
                detay=f"Palet pasife alındı: {palet.palet_no} (ID: {palet_id})",
            )
        )
