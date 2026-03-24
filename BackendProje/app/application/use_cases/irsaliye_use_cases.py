"""
İrsaliye Use Case'leri.

İş kuralları:
- İrsaliye oluşturulurken otomatik IRS-YYYY-NNNN numarası atanır.
- Sipariş kalemleri üzerinden stok çıkışı yapılır (sevkiyat henüz yüklenmediyse).
- Durum geçişleri domain entity metotları (kes, gonder) üzerinden doğrulanır.
- Her kritik işlemde sistem logu yazılır.
"""

from __future__ import annotations
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.repositories.irsaliye_repository import IIrsaliyeRepository
from app.core.repositories.siparis_repository import ISiparisRepository
from app.core.repositories.sevkiyat_plani_repository import ISevkiyatPlaniRepository
from app.core.repositories.sistem_log_repository import ISistemLogRepository
from app.core.services.stok_cikis_domain_service import StokCikisDomainService
from app.core.entities.irsaliye import Irsaliye, IrsaliyeDurum
from app.core.entities.sevkiyat_plani import SevkiyatDurum
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.exceptions import KayitBulunamadiError, GecersizDurumGecisiError
from app.application.dto.irsaliye_dto import (
    IrsaliyeOlusturRequestDTO,
    IrsaliyeGuncelleRequestDTO,
    IrsaliyeResponseDTO,
    IrsaliyeYazdirResponseDTO,
    IrsaliyeYazdirIrsaliyeDTO,
    IrsaliyeYazdirSiparisDTO,
    IrsaliyeYazdirKalemDTO,
)


# ─────────────────────────────────────────────────────────────────
# İRSALİYE LİSTELE
# ─────────────────────────────────────────────────────────────────

class IrsaliyeListeleUseCase:

    def __init__(self, irsaliye_repo: IIrsaliyeRepository):
        self._repo = irsaliye_repo

    def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        durum: Optional[str] = None,
        arama: Optional[str] = None,
    ) -> List[IrsaliyeResponseDTO]:
        irsaliyeler = self._repo.getir_hepsi(
            skip=skip, limit=limit, durum=durum, arama=arama
        )
        return [IrsaliyeResponseDTO.from_entity(i) for i in irsaliyeler]


# ─────────────────────────────────────────────────────────────────
# İRSALİYE GETİR
# ─────────────────────────────────────────────────────────────────

class IrsaliyeGetirUseCase:

    def __init__(self, irsaliye_repo: IIrsaliyeRepository):
        self._repo = irsaliye_repo

    def execute(self, irsaliye_id: int) -> IrsaliyeResponseDTO:
        irsaliye = self._repo.getir_id_ile(irsaliye_id)
        if not irsaliye:
            raise KayitBulunamadiError("İrsaliye", irsaliye_id)
        return IrsaliyeResponseDTO.from_entity(irsaliye)


# ─────────────────────────────────────────────────────────────────
# İRSALİYE OLUŞTUR
# ─────────────────────────────────────────────────────────────────

class IrsaliyeOlusturUseCase:
    """
    Yeni irsaliye oluşturur.

    İş kuralları:
    - Sipariş varlığı kontrol edilir.
    - Otomatik irsaliye numarası atanır. Durum her zaman Taslak başlar.
    - Sevkiyat planı yoksa veya henüz yüklemeye başlanmadıysa stok çıkışı yapılır.
    - Oluşturma logu yazılır.
    """

    def __init__(
        self,
        irsaliye_repo: IIrsaliyeRepository,
        siparis_repo: ISiparisRepository,
        sevkiyat_repo: ISevkiyatPlaniRepository,
        log_repo: ISistemLogRepository,
        stok_cikis_service: StokCikisDomainService,
        db: Session,
    ):
        self._irsaliye_repo = irsaliye_repo
        self._siparis_repo = siparis_repo
        self._sevkiyat_repo = sevkiyat_repo
        self._log_repo = log_repo
        self._stok_cikis = stok_cikis_service
        self._db = db

    def execute(
        self,
        dto: IrsaliyeOlusturRequestDTO,
        kullanici_id: int,
    ) -> IrsaliyeResponseDTO:
        siparis = self._siparis_repo.getir_id_ile(dto.siparis_id)
        if not siparis:
            raise KayitBulunamadiError("Sipariş", dto.siparis_id)

        irsaliye_no = self._irsaliye_repo.sonraki_irsaliye_no()

        irsaliye = Irsaliye(
            siparis_id=dto.siparis_id,
            sevkiyat_id=dto.sevkiyat_id,
            irsaliye_no=irsaliye_no,
            irsaliye_tarihi=dto.irsaliye_tarihi,
            belge_turu=dto.belge_turu,
            tir_plaka=dto.tir_plaka,
            sofor_adi=dto.sofor_adi,
        )

        try:
            kaydedilen = self._irsaliye_repo.olustur(irsaliye)

            self._log_repo.olustur(
                SistemLog.olustur(
                    kullanici_id=kullanici_id,
                    islem_tipi=IslemTipi.CREATE,
                    modul="İrsaliye Yönetimi",
                    detay=f"Yeni irsaliye oluşturuldu: {irsaliye_no}",
                ),
                auto_commit=False,
            )

            if not self._sevkiyat_stok_cikarildi_mi(dto.siparis_id) and siparis.kalemler:
                self._stok_cikis.siparis_bazli_stok_cikisi(
                    kalemler=siparis.kalemler,
                    siparis_no=siparis.siparis_no,
                    kullanici_id=kullanici_id,
                    tir_plaka=dto.tir_plaka,
                    aciklama_prefix=f"İrsaliye çıkışı - {irsaliye_no}",
                    modul="İrsaliye Yönetimi",
                )

            self._db.commit()
            return IrsaliyeResponseDTO.from_entity(kaydedilen)

        except Exception:
            self._db.rollback()
            raise

    def _sevkiyat_stok_cikarildi_mi(self, siparis_id: int) -> bool:
        plan = self._sevkiyat_repo.getir_siparis_id_ile(siparis_id)
        return plan is not None and SevkiyatDurum.stok_cikarilmis_mi(plan.durum)


# ─────────────────────────────────────────────────────────────────
# İRSALİYE GÜNCELLE
# ─────────────────────────────────────────────────────────────────

class IrsaliyeGuncelleUseCase:
    """
    İrsaliye bilgilerini ve durumunu günceller.

    İş kuralları:
    - İrsaliye bulunamazsa KayitBulunamadiError.
    - Durum değişimi domain entity metotları (kes/gonder) üzerinden doğrulanır.
    - Güncelleme logu yazılır.
    """

    def __init__(
        self,
        irsaliye_repo: IIrsaliyeRepository,
        log_repo: ISistemLogRepository,
    ):
        self._repo = irsaliye_repo
        self._log_repo = log_repo

    def execute(
        self,
        irsaliye_id: int,
        dto: IrsaliyeGuncelleRequestDTO,
        kullanici_id: int,
    ) -> IrsaliyeResponseDTO:
        irsaliye = self._repo.getir_id_ile(irsaliye_id)
        if not irsaliye:
            raise KayitBulunamadiError("İrsaliye", irsaliye_id)

        eski_durum = irsaliye.durum

        if dto.belge_turu is not None:
            irsaliye.belge_turu = dto.belge_turu
        if dto.tir_plaka is not None:
            irsaliye.tir_plaka = dto.tir_plaka
        if dto.sofor_adi is not None:
            irsaliye.sofor_adi = dto.sofor_adi

        if dto.durum is not None and dto.durum != eski_durum:
            if dto.durum == IrsaliyeDurum.KESILDI:
                irsaliye.kes()
            elif dto.durum == IrsaliyeDurum.GONDERILDI:
                irsaliye.gonder()
            else:
                raise GecersizDurumGecisiError("İrsaliye", eski_durum, dto.durum)

        kaydedilen = self._repo.guncelle(irsaliye)

        if dto.durum and dto.durum != eski_durum:
            self._log_repo.olustur(
                SistemLog.olustur(
                    kullanici_id=kullanici_id,
                    islem_tipi=IslemTipi.UPDATE,
                    modul="İrsaliye Yönetimi",
                    detay=f"İrsaliye durumu değiştirildi. Durum: {eski_durum} → {dto.durum}",
                )
            )

        return IrsaliyeResponseDTO.from_entity(kaydedilen)


# ─────────────────────────────────────────────────────────────────
# İRSALİYE YAZDIR VERİSİ
# ─────────────────────────────────────────────────────────────────

class IrsaliyeYazdirVerisiGetirUseCase:
    """İrsaliye yazdırma verisi: irsaliye + sipariş + kalemler."""

    def __init__(
        self,
        irsaliye_repo: IIrsaliyeRepository,
        siparis_repo: ISiparisRepository,
    ):
        self._irsaliye_repo = irsaliye_repo
        self._siparis_repo = siparis_repo

    def execute(self, irsaliye_id: int) -> IrsaliyeYazdirResponseDTO:
        irsaliye = self._irsaliye_repo.getir_id_ile(irsaliye_id)
        if not irsaliye:
            raise KayitBulunamadiError("İrsaliye", irsaliye_id)

        siparis = self._siparis_repo.getir_id_ile(irsaliye.siparis_id)

        irsaliye_dto = IrsaliyeYazdirIrsaliyeDTO(
            id=irsaliye.id,
            irsaliye_no=irsaliye.irsaliye_no,
            irsaliye_tarihi=str(irsaliye.irsaliye_tarihi),
            belge_turu=irsaliye.belge_turu,
            tir_plaka=irsaliye.tir_plaka,
            sofor_adi=irsaliye.sofor_adi,
            durum=irsaliye.durum,
        )

        if siparis:
            siparis_dto = IrsaliyeYazdirSiparisDTO(
                siparis_no=siparis.siparis_no,
                musteri_adi=siparis.musteri_adi,
                teslimat_adresi=siparis.teslimat_adresi,
                teslimat_tarihi=str(siparis.teslimat_tarihi),
                top_tutar=siparis.top_tutar,
                top_miktar=siparis.top_miktar,
            )
            kalemler = [
                IrsaliyeYazdirKalemDTO(
                    urun_id=k.urun_id,
                    urun_isim=getattr(k, "urun_isim", "-"),
                    miktar=k.miktar,
                    birim_fiyat=k.birim_fiyat,
                    kdv_orani=k.kdv_orani,
                    toplam=k.toplam,
                )
                for k in siparis.kalemler
            ]
        else:
            siparis_dto = IrsaliyeYazdirSiparisDTO(
                siparis_no="-", musteri_adi="-", teslimat_adresi="-",
                teslimat_tarihi="-", top_tutar=0, top_miktar=0,
            )
            kalemler = []

        return IrsaliyeYazdirResponseDTO(
            irsaliye=irsaliye_dto,
            siparis=siparis_dto,
            kalemler=kalemler,
        )
