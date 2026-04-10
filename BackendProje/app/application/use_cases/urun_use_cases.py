"""
Ürün Use Case'leri.

Her sınıf tek bir iş eylemini temsil eder; bağımlılıklar sadece
core/repositories içindeki soyut arayüzlerden oluşur.
"""

from __future__ import annotations
from datetime import datetime
from typing import List, Optional

from app.core.repositories.urun_repository import IUrunRepository
from app.core.repositories.sistem_log_repository import ISistemLogRepository
from app.core.entities.urun import Urun
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.exceptions import (
    KayitBulunamadiError,
    CakismaHatasi,
)
from app.application.dto.urun_dto import (
    UrunOlusturRequestDTO,
    UrunGuncelleRequestDTO,
    UrunResponseDTO,
    UrunListResponseDTO,
)


# ─────────────────────────────────────────────────────────────────
# ÜRÜN LİSTELE
# ─────────────────────────────────────────────────────────────────

class UrunListeleUseCase:
    """Ürün listesini filtreleyerek döner."""

    def __init__(self, urun_repo: IUrunRepository):
        self._urun_repo = urun_repo

    def execute(
        self,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None,
        kategori_id: Optional[int] = None,
        marka_id: Optional[int] = None,
    ) -> List[UrunListResponseDTO]:
        urunler = self._urun_repo.getir_hepsi(
            skip=skip, limit=limit,
            search=search,
            kategori_id=kategori_id,
            marka_id=marka_id,
        )
        return [UrunListResponseDTO.from_entity(u) for u in urunler]


# ─────────────────────────────────────────────────────────────────
# ÜRÜN GETİR
# ─────────────────────────────────────────────────────────────────

class UrunGetirUseCase:
    """ID veya barkod ile tek ürün getirir; bulamazsa hata fırlatır."""

    def __init__(self, urun_repo: IUrunRepository):
        self._urun_repo = urun_repo

    def by_id(self, urun_id: int) -> UrunResponseDTO:
        urun = self._urun_repo.getir_id_ile(urun_id)
        if not urun:
            raise KayitBulunamadiError("Ürün", urun_id)
        return UrunResponseDTO.from_entity(urun)

    def by_barkod(self, barkod: str) -> UrunResponseDTO:
        urun = self._urun_repo.getir_barkod_ile(barkod)
        if not urun:
            raise KayitBulunamadiError("Barkod", barkod)
        return UrunResponseDTO.from_entity(urun)


# ─────────────────────────────────────────────────────────────────
# KRİTİK ÜRÜNLER
# ─────────────────────────────────────────────────────────────────

class KritikUrunleriGetirUseCase:
    """Min stok eşiğinin altındaki ürünleri döner."""

    def __init__(self, urun_repo: IUrunRepository):
        self._urun_repo = urun_repo

    def execute(self) -> List[UrunListResponseDTO]:
        urunler = self._urun_repo.getir_kritik_stoklar()
        return [UrunListResponseDTO.from_entity(u) for u in urunler]


# ─────────────────────────────────────────────────────────────────
# ÜRÜN OLUŞTUR
# ─────────────────────────────────────────────────────────────────

class UrunOlusturUseCase:
    """
    Yeni ürün oluşturur.

    İş kuralları:
    - Barkod benzersiz olmalı (varsa).
    - Oluşturma logu yazılır.
    """

    def __init__(
        self,
        urun_repo: IUrunRepository,
        log_repo: ISistemLogRepository,
    ):
        self._urun_repo = urun_repo
        self._log_repo = log_repo

    def execute(self, dto: UrunOlusturRequestDTO, kullanici_id: int) -> UrunResponseDTO:
        # 1. Barkod çakışma kontrolü
        if dto.barkod:
            mevcut = self._urun_repo.getir_barkod_ile(dto.barkod)
            if mevcut:
                raise CakismaHatasi("Barkod", dto.barkod)

        # 1b. EAN çakışma kontrolü
        if dto.ean:
            mevcut_ean = self._urun_repo.getir_ean_ile(dto.ean)
            if mevcut_ean:
                raise CakismaHatasi("EAN", dto.ean)

        # 2. Domain entity oluştur
        urun = Urun(
            isim=dto.isim,
            marka_id=dto.marka_id,
            kategori_id=dto.kategori_id,
            tedarikci_id=dto.tedarikci_id,
            ean=dto.ean,
            barkod=dto.barkod,
            ic_adet=dto.ic_adet,
            gramaj=dto.gramaj,
            birim=dto.birim,
            fiyat=dto.fiyat,
            min_stok=dto.min_stok,
            aciklama=dto.aciklama,
            depolama_tipi=dto.depolama_tipi,
        )

        # 3. Kaydet
        kaydedilen = self._urun_repo.olustur(urun)

        # 4. Sistem logu
        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.CREATE,
                modul="Ürün Yönetimi",
                detay=f"Yeni ürün eklendi: {kaydedilen.isim} (Barkod: {kaydedilen.barkod or '-'})",
                yeni_veri={"isim": kaydedilen.isim, "fiyat": kaydedilen.fiyat},
            )
        )

        return UrunResponseDTO.from_entity(kaydedilen)


# ─────────────────────────────────────────────────────────────────
# ÜRÜN GÜNCELLE
# ─────────────────────────────────────────────────────────────────

class UrunGuncelleUseCase:
    """
    Mevcut ürünü günceller.

    İş kuralları:
    - Ürün bulunamazsa KayitBulunamadiError.
    - Barkod değiştiriliyorsa benzersiz olmalı.
    - Güncelleme logu yazılır.
    """

    def __init__(
        self,
        urun_repo: IUrunRepository,
        log_repo: ISistemLogRepository,
    ):
        self._urun_repo = urun_repo
        self._log_repo = log_repo

    def execute(
        self,
        urun_id: int,
        dto: UrunGuncelleRequestDTO,
        kullanici_id: int,
    ) -> UrunResponseDTO:
        # 1. Varlık kontrolü
        mevcut = self._urun_repo.getir_id_ile(urun_id)
        if not mevcut:
            raise KayitBulunamadiError("Ürün", urun_id)

        # 2. Barkod çakışma kontrolü (farklı ürüne aitse)
        if dto.barkod and dto.barkod != mevcut.barkod:
            sahip = self._urun_repo.getir_barkod_ile(dto.barkod)
            if sahip and sahip.id != urun_id:
                raise CakismaHatasi("Barkod", dto.barkod)

        # 2b. EAN çakışma kontrolü (farklı ürüne aitse)
        if dto.ean and dto.ean != mevcut.ean:
            sahip_ean = self._urun_repo.getir_ean_ile(dto.ean)
            if sahip_ean and sahip_ean.id != urun_id:
                raise CakismaHatasi("EAN", dto.ean)

        # 3. Değişiklik snapshot'ı (log için)
        eski_veri = {"isim": mevcut.isim, "fiyat": mevcut.fiyat}

        # 4. Entity'yi güncelle (sadece gönderilen alanları)
        guncel_veri = dto.model_dump(exclude_unset=True)
        for alan, deger in guncel_veri.items():
            setattr(mevcut, alan, deger)
        mevcut.guncelleme_tarihi = datetime.utcnow()

        # 5. Kaydet
        kaydedilen = self._urun_repo.guncelle(mevcut)

        # 6. Sistem logu
        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Ürün Yönetimi",
                detay=f"Ürün güncellendi: {kaydedilen.isim}",
                eski_veri=eski_veri,
                yeni_veri={"isim": kaydedilen.isim, "fiyat": kaydedilen.fiyat},
            )
        )

        return UrunResponseDTO.from_entity(kaydedilen)


# ─────────────────────────────────────────────────────────────────
# ÜRÜN SİL (soft delete)
# ─────────────────────────────────────────────────────────────────

class UrunSilUseCase:
    """
    Ürünü pasife alır (aktif=False).

    İş kuralları:
    - Ürün bulunamazsa KayitBulunamadiError.
    - Silme logu yazılır.
    """

    def __init__(
        self,
        urun_repo: IUrunRepository,
        log_repo: ISistemLogRepository,
    ):
        self._urun_repo = urun_repo
        self._log_repo = log_repo

    def execute(self, urun_id: int, kullanici_id: int) -> None:
        urun = self._urun_repo.getir_id_ile(urun_id)
        if not urun:
            raise KayitBulunamadiError("Ürün", urun_id)

        self._urun_repo.sil(urun_id)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.DELETE,
                modul="Ürün Yönetimi",
                detay=f"Ürün pasife alındı: {urun.isim} (ID: {urun_id})",
            )
        )
