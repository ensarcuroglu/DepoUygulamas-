"""
Stok Sayım Use Case'leri.

İş kuralları:
- Sayım başlatılırken mevcut stok durumu snapshot olarak kaydedilir.
- Kalem kaydetme upsert mantığıyla çalışır (aynı ürün tekrar tarandığında güncellenir).
- Durum geçişleri domain entity metotları (baslat, bitir, onayla) üzerinden doğrulanır.
- Varyans hesaplamasında sadece sapmalı ürünler raporlanır.
- Her kritik işlemde sistem logu yazılır.
"""

from __future__ import annotations
from datetime import datetime
from typing import List

from app.core.repositories.stok_sayim_repository import IStokSayimRepository
from app.core.repositories.urun_repository import IUrunRepository
from app.core.repositories.sistem_log_repository import ISistemLogRepository
from app.core.entities.stok_sayim import StokSayim, StokSayimKalemi, SayimDurum
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.exceptions import KayitBulunamadiError, GecersizIslemError
from app.application.dto.stok_sayim_dto import (
    StokSayimOlusturRequestDTO,
    StokSayimKalemiKaydetRequestDTO,
    StokSayimResponseDTO,
    StokSayimKalemiResponseDTO,
    VaryansResponseDTO,
    VaryansKalemDTO,
)


# ─────────────────────────────────────────────────────────────────
# SAYIM LİSTELE
# ─────────────────────────────────────────────────────────────────

class StokSayimListeleUseCase:

    def __init__(self, sayim_repo: IStokSayimRepository):
        self._repo = sayim_repo

    def execute(self, skip: int = 0, limit: int = 100) -> List[StokSayimResponseDTO]:
        sayimlar = self._repo.getir_hepsi(skip=skip, limit=limit)
        return [StokSayimResponseDTO.from_entity(s) for s in sayimlar]


# ─────────────────────────────────────────────────────────────────
# SAYIM GETİR
# ─────────────────────────────────────────────────────────────────

class StokSayimGetirUseCase:

    def __init__(self, sayim_repo: IStokSayimRepository):
        self._repo = sayim_repo

    def execute(self, sayim_id: int) -> StokSayimResponseDTO:
        sayim = self._repo.getir_id_ile(sayim_id)
        if not sayim:
            raise KayitBulunamadiError("Sayım", sayim_id)
        return StokSayimResponseDTO.from_entity(sayim)


# ─────────────────────────────────────────────────────────────────
# SAYIM BAŞLAT (oluştur + stok snapshot)
# ─────────────────────────────────────────────────────────────────

class StokSayimBaslatUseCase:
    """
    Yeni stok sayımı başlatır.

    İş kuralları:
    - Benzersiz sayim_no üretir (SAY-YYYYMMDD-HHMM).
    - Aktif tüm ürünlerin stok snapshot'ını alır (referans_stok_json).
    - Oluşturma logu yazılır.
    """

    def __init__(
        self,
        sayim_repo: IStokSayimRepository,
        log_repo: ISistemLogRepository,
    ):
        self._repo = sayim_repo
        self._log_repo = log_repo

    def execute(
        self,
        dto: StokSayimOlusturRequestDTO,
        kullanici_id: int,
    ) -> StokSayimResponseDTO:
        if self._repo.aktif_sayim_var_mi():
            raise GecersizIslemError("Zaten aktif bir sayım mevcut. Önce mevcut sayımı tamamlayın.")

        now = datetime.utcnow()
        sayim_no = f"SAY-{now.year}{now.month:02d}-{now.day:02d}-{now.hour:02d}{now.minute:02d}{now.second:02d}"

        referans_stok = self._repo.stok_snapshot_getir()
        # JSON serialization requires string keys; DB returns int keys
        referans_stok_json = {str(k): v for k, v in referans_stok.items()}

        sayim = StokSayim(
            sayim_no=sayim_no,
            aciklama=dto.aciklama,
            kontrol_eden_user_id=kullanici_id,
            referans_stok_json=referans_stok_json,
        )
        sayim.baslat()

        kaydedilen = self._repo.olustur(sayim)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.CREATE,
                modul="Stok Sayım",
                detay=f"Yeni stok sayımı başlatıldı: {sayim_no}",
            )
        )

        return StokSayimResponseDTO.from_entity(kaydedilen)


# ─────────────────────────────────────────────────────────────────
# KALEM KAYDET (UPSERT)
# ─────────────────────────────────────────────────────────────────

class StokSayimKalemKaydetUseCase:
    """
    Sayım kalemi kaydeder (upsert).

    İş kuralları:
    - Sayım aktif (devam_ediyor veya oluşturuldu) olmalı.
    - Ürün varlığı kontrol edilir.
    - Aynı ürün tekrar tarandığında miktar güncellenir.
    """

    def __init__(
        self,
        sayim_repo: IStokSayimRepository,
        urun_repo: IUrunRepository,
    ):
        self._sayim_repo = sayim_repo
        self._urun_repo = urun_repo

    def execute(
        self,
        sayim_id: int,
        dto: StokSayimKalemiKaydetRequestDTO,
        kullanici_id: int,
    ) -> StokSayimKalemiResponseDTO:
        sayim = self._sayim_repo.getir_id_ile(sayim_id)
        if not sayim:
            raise KayitBulunamadiError("Sayım", sayim_id)

        if sayim.durum not in (SayimDurum.OLUSTURULDU, SayimDurum.DEVAM_EDIYOR):
            raise GecersizIslemError("Bu sayım aktif değil")

        if dto.ean:
            urun = self._urun_repo.getir_barkod_ile(dto.ean)
            if not urun:
                raise KayitBulunamadiError("Ürün (EAN/Barkod)", dto.ean)
        else:
            urun = self._urun_repo.getir_id_ile(dto.urun_id)
            if not urun:
                raise KayitBulunamadiError("Ürün", dto.urun_id)

        mevcut_kalem = self._sayim_repo.kalem_getir_by_sayim_urun(sayim_id, urun.id)

        if mevcut_kalem:
            mevcut_kalem.sayilan_miktar = dto.sayilan_miktar
            mevcut_kalem.notlar = dto.notlar
            mevcut_kalem.sayim_tarihi = datetime.utcnow()
            kaydedilen = self._sayim_repo.kalem_guncelle(mevcut_kalem)
        else:
            yeni_kalem = StokSayimKalemi(
                sayim_id=sayim_id,
                urun_id=urun.id,
                sayilan_miktar=dto.sayilan_miktar,
                notlar=dto.notlar,
                user_id=kullanici_id,
            )
            kaydedilen = self._sayim_repo.kalem_ekle(yeni_kalem)

        return StokSayimKalemiResponseDTO.from_entity(kaydedilen, urun_adi=urun.isim)


# ─────────────────────────────────────────────────────────────────
# VARYANS HESAPLA
# ─────────────────────────────────────────────────────────────────

class StokSayimVaryansHesaplaUseCase:
    """Referans stok ile sayılan miktarı karşılaştırır. Sadece sapmalı ürünleri döner."""

    def __init__(
        self,
        sayim_repo: IStokSayimRepository,
        urun_repo: IUrunRepository,
    ):
        self._sayim_repo = sayim_repo
        self._urun_repo = urun_repo

    def execute(self, sayim_id: int) -> VaryansResponseDTO:
        sayim = self._sayim_repo.getir_id_ile(sayim_id)
        if not sayim:
            raise KayitBulunamadiError("Sayım", sayim_id)

        if not sayim.referans_stok_json:
            return VaryansResponseDTO(sayim_no=sayim.sayim_no)

        # Kalemler zaten eagerly yüklü — N+1 yerine in-memory lookup
        kalem_map = {k.urun_id: k for k in sayim.sayim_kalemleri}

        # Sapmalı ürün ID'lerini topla, sonra tek seferde isimleri çek
        varyans_veriler = []
        toplam_fark = 0

        for urun_id_str, beklenen in sayim.referans_stok_json.items():
            urun_id = int(urun_id_str)
            kalem = kalem_map.get(urun_id)
            sayilan = kalem.sayilan_miktar if kalem else 0
            fark = sayilan - beklenen

            if abs(fark) > 0:
                varyans_veriler.append((urun_id, beklenen, sayilan, fark, kalem))
                toplam_fark += abs(fark)

        # Ürün isimlerini tek seferde çek
        urun_map = {}
        for urun_id, *_ in varyans_veriler:
            if urun_id not in urun_map:
                urun = self._urun_repo.getir_id_ile(urun_id)
                urun_map[urun_id] = urun.isim if urun else f"Ürün #{urun_id}"

        varyanslar = [
            VaryansKalemDTO(
                urun_id=urun_id,
                urun_adi=urun_map[urun_id],
                beklenen=beklenen,
                sayilan=sayilan,
                fark=fark,
                yuzde=round(fark / beklenen * 100, 1) if beklenen > 0 else 0,
                notlar=kalem.notlar if kalem else "",
            )
            for urun_id, beklenen, sayilan, fark, kalem in varyans_veriler
        ]

        return VaryansResponseDTO(
            sayim_no=sayim.sayim_no,
            referans_tarih=sayim.baslangic_tarihi,
            varyanslar=varyanslar,
            toplam_sapma=toplam_fark,
            sayilan_urun_sayisi=len(sayim.sayim_kalemleri),
            sapma_orani=round(
                len(varyanslar) / len(sayim.referans_stok_json) * 100, 1
            ) if sayim.referans_stok_json else 0,
        )


# ─────────────────────────────────────────────────────────────────
# SAYIM BİTİR
# ─────────────────────────────────────────────────────────────────

class StokSayimBitirUseCase:
    """
    Sayımı bitirir (devam_ediyor → bitti).

    İş kuralları:
    - Domain entity bitir() metodu durum geçişini doğrular.
    - Bitiş logu yazılır.
    """

    def __init__(
        self,
        sayim_repo: IStokSayimRepository,
        log_repo: ISistemLogRepository,
    ):
        self._repo = sayim_repo
        self._log_repo = log_repo

    def execute(self, sayim_id: int, kullanici_id: int) -> dict:
        sayim = self._repo.getir_id_ile(sayim_id)
        if not sayim:
            raise KayitBulunamadiError("Sayım", sayim_id)

        sayim.bitir()
        self._repo.guncelle(sayim)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Stok Sayım",
                detay=f"Stok sayımı bitirildi: {sayim.sayim_no}",
            )
        )

        return {"message": "Sayım bitirildi", "sayim_no": sayim.sayim_no}


# ─────────────────────────────────────────────────────────────────
# SAYIM ONAYLA
# ─────────────────────────────────────────────────────────────────

class StokSayimOnaylaUseCase:
    """
    Sayımı onaylar.

    İş kuralları:
    - Domain entity onayla() metodu durum geçişini doğrular.
    - Onay logu yazılır.
    """

    def __init__(
        self,
        sayim_repo: IStokSayimRepository,
        log_repo: ISistemLogRepository,
    ):
        self._repo = sayim_repo
        self._log_repo = log_repo

    def execute(self, sayim_id: int, kullanici_id: int) -> dict:
        sayim = self._repo.getir_id_ile(sayim_id)
        if not sayim:
            raise KayitBulunamadiError("Sayım", sayim_id)

        sayim.onayla(onaylayan_user_id=kullanici_id)
        self._repo.guncelle(sayim)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Stok Sayım",
                detay=f"Stok sayımı onaylandı: {sayim.sayim_no}",
            )
        )

        return {"message": "Sayım onaylandı", "sayim_no": sayim.sayim_no}
