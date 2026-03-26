"""
Mal Kabul İrsaliyesi Use Case'leri.

Mal kabul belgesi CRUD + durum geçişleri.
Kalemler (palet tanımları) irsaliye ile birlikte yönetilir.
"""

from __future__ import annotations
from typing import List, Optional

from app.core.repositories.mal_kabul_irsaliye_repository import IMalKabulIrsaliyeRepository
from app.core.repositories.tedarikci_repository import ITedarikciRepository
from app.core.repositories.depo_repository import IDepoRepository
from app.core.repositories.urun_repository import IUrunRepository
from app.core.repositories.sistem_log_repository import ISistemLogRepository
from app.core.entities.mal_kabul_irsaliye import (
    MalKabulIrsaliye,
    MalKabulKalemi,
    MalKabulDurum,
)
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.exceptions import KayitBulunamadiError, GecersizDurumGecisiError, GecersizIslemError
from app.application.dto.mal_kabul_irsaliye_dto import (
    MalKabulIrsaliyeOlusturRequestDTO,
    MalKabulIrsaliyeGuncelleRequestDTO,
    MalKabulIrsaliyeResponseDTO,
    MalKabulKalemiOlusturDTO,
)


def _dto_to_kalem_entity(dto: MalKabulKalemiOlusturDTO) -> MalKabulKalemi:
    return MalKabulKalemi(
        palet_no=dto.palet_no,
        urun_id=dto.urun_id,
        lot_no=dto.lot_no,
        miktar=dto.miktar,
        raf_id=dto.raf_id,
        uretim_tarihi=dto.uretim_tarihi,
        son_kullanma_tarihi=dto.son_kullanma_tarihi,
    )


def _urunleri_dogrula(urun_repo: IUrunRepository, kalem_dtolar: list[MalKabulKalemiOlusturDTO]) -> None:
    urun_idler = {k.urun_id for k in kalem_dtolar}
    for urun_id in urun_idler:
        if not urun_repo.getir_id_ile(urun_id):
            raise KayitBulunamadiError("Ürün", urun_id)


# ─────────────────────────────────────────────────────────────────
# LİSTELE
# ─────────────────────────────────────────────────────────────────

class MalKabulIrsaliyeListeleUseCase:

    def __init__(self, repo: IMalKabulIrsaliyeRepository):
        self._repo = repo

    def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        durum: Optional[str] = None,
        arama: Optional[str] = None,
        depo_id: Optional[int] = None,
        tedarikci_id: Optional[int] = None,
    ) -> List[MalKabulIrsaliyeResponseDTO]:
        irsaliyeler = self._repo.getir_hepsi(
            skip=skip, limit=limit, durum=durum, arama=arama,
            depo_id=depo_id, tedarikci_id=tedarikci_id,
        )
        return [MalKabulIrsaliyeResponseDTO.from_entity(i) for i in irsaliyeler]


# ─────────────────────────────────────────────────────────────────
# GETİR
# ─────────────────────────────────────────────────────────────────

class MalKabulIrsaliyeGetirUseCase:

    def __init__(self, repo: IMalKabulIrsaliyeRepository):
        self._repo = repo

    def execute(self, irsaliye_id: int) -> MalKabulIrsaliyeResponseDTO:
        irsaliye = self._repo.getir_id_ile(irsaliye_id)
        if not irsaliye:
            raise KayitBulunamadiError("Mal Kabul İrsaliyesi", irsaliye_id)
        return MalKabulIrsaliyeResponseDTO.from_entity(irsaliye)


# ─────────────────────────────────────────────────────────────────
# OLUŞTUR
# ─────────────────────────────────────────────────────────────────

class MalKabulIrsaliyeOlusturUseCase:

    def __init__(
        self,
        repo: IMalKabulIrsaliyeRepository,
        tedarikci_repo: ITedarikciRepository,
        depo_repo: IDepoRepository,
        urun_repo: IUrunRepository,
        log_repo: ISistemLogRepository,
    ):
        self._repo = repo
        self._tedarikci_repo = tedarikci_repo
        self._depo_repo = depo_repo
        self._urun_repo = urun_repo
        self._log_repo = log_repo

    def execute(
        self,
        dto: MalKabulIrsaliyeOlusturRequestDTO,
        kullanici_id: int,
    ) -> MalKabulIrsaliyeResponseDTO:
        # Ön koşullar
        tedarikci = self._tedarikci_repo.getir_id_ile(dto.tedarikci_id)
        if not tedarikci:
            raise KayitBulunamadiError("Tedarikçi", dto.tedarikci_id)

        depo = self._depo_repo.getir_id_ile(dto.depo_id)
        if not depo:
            raise KayitBulunamadiError("Depo", dto.depo_id)

        # Kalem ürünlerini doğrula (deduplicated)
        _urunleri_dogrula(self._urun_repo, dto.kalemler)

        # Entity oluştur
        irsaliye_no = self._repo.sonraki_irsaliye_no()
        kalemler = [_dto_to_kalem_entity(k) for k in dto.kalemler]

        irsaliye = MalKabulIrsaliye(
            irsaliye_no=irsaliye_no,
            tedarikci_id=dto.tedarikci_id,
            depo_id=dto.depo_id,
            tarih=dto.tarih,
            tir_plaka=dto.tir_plaka,
            sofor_adi=dto.sofor_adi,
            kalemler=kalemler,
        )

        kaydedilen = self._repo.olustur(irsaliye)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.CREATE,
                modul="Mal Kabul İrsaliyesi",
                detay=f"Yeni mal kabul irsaliyesi: {irsaliye_no} | {len(kalemler)} kalem",
            )
        )

        return MalKabulIrsaliyeResponseDTO.from_entity(kaydedilen)


# ─────────────────────────────────────────────────────────────────
# GÜNCELLE
# ─────────────────────────────────────────────────────────────────

class MalKabulIrsaliyeGuncelleUseCase:

    def __init__(
        self,
        repo: IMalKabulIrsaliyeRepository,
        urun_repo: IUrunRepository,
        log_repo: ISistemLogRepository,
    ):
        self._repo = repo
        self._urun_repo = urun_repo
        self._log_repo = log_repo

    def execute(
        self,
        irsaliye_id: int,
        dto: MalKabulIrsaliyeGuncelleRequestDTO,
        kullanici_id: int,
    ) -> MalKabulIrsaliyeResponseDTO:
        irsaliye = self._repo.getir_id_ile(irsaliye_id)
        if not irsaliye:
            raise KayitBulunamadiError("Mal Kabul İrsaliyesi", irsaliye_id)

        eski_durum = irsaliye.durum

        # Durum geçişi
        if dto.durum is not None and dto.durum != eski_durum:
            try:
                irsaliye.durum_degistir(dto.durum)
            except ValueError as e:
                raise GecersizDurumGecisiError(
                    "Mal Kabul İrsaliyesi", eski_durum, dto.durum
                ) from e

        # Basit alan güncellemeleri (sadece taslakta)
        if eski_durum == MalKabulDurum.TASLAK:
            if dto.tedarikci_id is not None:
                irsaliye.tedarikci_id = dto.tedarikci_id
            if dto.depo_id is not None:
                irsaliye.depo_id = dto.depo_id
            if dto.tarih is not None:
                irsaliye.tarih = dto.tarih
            if dto.tir_plaka is not None:
                irsaliye.tir_plaka = dto.tir_plaka
            if dto.sofor_adi is not None:
                irsaliye.sofor_adi = dto.sofor_adi

            # Kalem güncellemesi
            if dto.kalemler is not None:
                _urunleri_dogrula(self._urun_repo, dto.kalemler)
                irsaliye.kalemler = [_dto_to_kalem_entity(k) for k in dto.kalemler]

        kaydedilen = self._repo.guncelle(irsaliye)

        # Durum değişikliği loglama
        if dto.durum and dto.durum != eski_durum:
            self._log_repo.olustur(
                SistemLog.olustur(
                    kullanici_id=kullanici_id,
                    islem_tipi=IslemTipi.UPDATE,
                    modul="Mal Kabul İrsaliyesi",
                    detay=f"İrsaliye durumu: {eski_durum} → {dto.durum} | {irsaliye.irsaliye_no}",
                )
            )

        return MalKabulIrsaliyeResponseDTO.from_entity(kaydedilen)


# ─────────────────────────────────────────────────────────────────
# SİL
# ─────────────────────────────────────────────────────────────────

class MalKabulIrsaliyeSilUseCase:

    def __init__(
        self,
        repo: IMalKabulIrsaliyeRepository,
        log_repo: ISistemLogRepository,
    ):
        self._repo = repo
        self._log_repo = log_repo

    def execute(self, irsaliye_id: int, kullanici_id: int) -> bool:
        irsaliye = self._repo.getir_id_ile(irsaliye_id)
        if not irsaliye:
            raise KayitBulunamadiError("Mal Kabul İrsaliyesi", irsaliye_id)

        if not irsaliye.duzenlenebilir_mi():
            raise GecersizIslemError(
                f"Sadece taslak durumundaki irsaliyeler silinebilir. Mevcut durum: {irsaliye.durum}"
            )

        silindi = self._repo.sil(irsaliye_id)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.DELETE,
                modul="Mal Kabul İrsaliyesi",
                detay=f"İrsaliye silindi: {irsaliye.irsaliye_no}",
            )
        )

        return silindi
