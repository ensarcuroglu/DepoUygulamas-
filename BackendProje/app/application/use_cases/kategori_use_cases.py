"""
Kategori Use Case'leri.
"""

from __future__ import annotations
from typing import List

from app.core.repositories.kategori_repository import IKategoriRepository
from app.core.repositories.sistem_log_repository import ISistemLogRepository
from app.core.entities.kategori import Kategori
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.exceptions import KayitBulunamadiError, CakismaHatasi
from app.application.dto.kategori_dto import (
    KategoriOlusturRequestDTO,
    KategoriGuncelleRequestDTO,
    KategoriResponseDTO,
)


class KategoriListeleUseCase:
    """Kategori listesini döner."""

    def __init__(self, kategori_repo: IKategoriRepository):
        self._kategori_repo = kategori_repo

    def execute(self, skip: int = 0, limit: int = 100) -> List[KategoriResponseDTO]:
        kategoriler = self._kategori_repo.getir_hepsi(skip=skip, limit=limit)
        return [KategoriResponseDTO.from_entity(k) for k in kategoriler]


class KategoriGetirUseCase:
    """ID ile tek kategori getirir."""

    def __init__(self, kategori_repo: IKategoriRepository):
        self._kategori_repo = kategori_repo

    def execute(self, kategori_id: int) -> KategoriResponseDTO:
        kategori = self._kategori_repo.getir_id_ile(kategori_id)
        if not kategori:
            raise KayitBulunamadiError("Kategori", kategori_id)
        return KategoriResponseDTO.from_entity(kategori)


class KategoriOlusturUseCase:
    """Yeni kategori oluşturur. İsim benzersiz olmalı."""

    def __init__(self, kategori_repo: IKategoriRepository, log_repo: ISistemLogRepository):
        self._kategori_repo = kategori_repo
        self._log_repo = log_repo

    def execute(self, dto: KategoriOlusturRequestDTO, kullanici_id: int) -> KategoriResponseDTO:
        mevcut = self._kategori_repo.getir_isim_ile(dto.isim)
        if mevcut:
            raise CakismaHatasi("Kategori adı", dto.isim)

        kategori = Kategori(isim=dto.isim, aciklama=dto.aciklama)
        kaydedilen = self._kategori_repo.olustur(kategori)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.CREATE,
                modul="Kategori Yönetimi",
                detay=f"Yeni kategori eklendi: {kaydedilen.isim}",
                yeni_veri={"isim": kaydedilen.isim},
            )
        )

        return KategoriResponseDTO.from_entity(kaydedilen)


class KategoriGuncelleUseCase:
    """Mevcut kategoriyi günceller."""

    def __init__(self, kategori_repo: IKategoriRepository, log_repo: ISistemLogRepository):
        self._kategori_repo = kategori_repo
        self._log_repo = log_repo

    def execute(
        self, kategori_id: int, dto: KategoriGuncelleRequestDTO, kullanici_id: int
    ) -> KategoriResponseDTO:
        mevcut = self._kategori_repo.getir_id_ile(kategori_id)
        if not mevcut:
            raise KayitBulunamadiError("Kategori", kategori_id)

        eski_veri = {"isim": mevcut.isim}

        # İsim değişiyorsa çakışma kontrolü
        guncel_veri = dto.model_dump(exclude_unset=True)
        yeni_isim = guncel_veri.get("isim")
        if yeni_isim and yeni_isim.lower() != mevcut.isim.lower():
            sahip = self._kategori_repo.getir_isim_ile(yeni_isim)
            if sahip and sahip.id != kategori_id:
                raise CakismaHatasi("Kategori adı", yeni_isim)

        for alan, deger in guncel_veri.items():
            setattr(mevcut, alan, deger)

        kaydedilen = self._kategori_repo.guncelle(mevcut)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Kategori Yönetimi",
                detay=f"Kategori güncellendi: {kaydedilen.isim}",
                eski_veri=eski_veri,
                yeni_veri={"isim": kaydedilen.isim},
            )
        )

        return KategoriResponseDTO.from_entity(kaydedilen)


class KategoriSilUseCase:
    """Kategoriyi pasife alır (soft delete)."""

    def __init__(self, kategori_repo: IKategoriRepository, log_repo: ISistemLogRepository):
        self._kategori_repo = kategori_repo
        self._log_repo = log_repo

    def execute(self, kategori_id: int, kullanici_id: int) -> None:
        kategori = self._kategori_repo.getir_id_ile(kategori_id)
        if not kategori:
            raise KayitBulunamadiError("Kategori", kategori_id)

        self._kategori_repo.sil(kategori_id)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.DELETE,
                modul="Kategori Yönetimi",
                detay=f"Kategori pasife alındı: {kategori.isim} (ID: {kategori_id})",
            )
        )
