"""
Palet Rezervasyonu Use Case'leri.

Rezervasyon yaşam döngüsü:
  Sipariş Hazırlanıyor → RezervasyonBaslatUseCase → Aktif rezervasyonlar
  Sipariş İptal       → RezervasyonIptalUseCase  → toplu IptalEdildi
  Sevkiyat Tamamlandi → RezervasyonKesinlestirUseCase → toplu Kesinlesti
  Admin değişim       → RezervasyonDegistirUseCase → eski iptal + yeni Aktif
"""

from __future__ import annotations
from typing import List, Optional

from app.core.repositories.palet_rezervasyonu_repository import IPaletRezervasyonuRepository
from app.core.repositories.palet_repository import IPaletRepository
from app.core.repositories.siparis_repository import ISiparisRepository
from app.core.repositories.sistem_log_repository import ISistemLogRepository
from app.core.entities.palet_rezervasyonu import PaletRezervasyonu, RezervasyonDurum
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.exceptions import KayitBulunamadiError, GecersizIslemError, YetersizStokError
from app.core.services.fefo_secim_servisi import FEFOSecimServisi
from app.application.dto.palet_rezervasyonu_dto import (
    PaletRezervasyonuResponseDTO,
    StokDetayResponseDTO,
)


# ─────────────────────────────────────────────────────────────────
# REZERVASYON LİSTELE
# ─────────────────────────────────────────────────────────────────

class PaletRezervasyonuListeleUseCase:

    def __init__(self, rezervasyon_repo: IPaletRezervasyonuRepository):
        self._repo = rezervasyon_repo

    def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        durum: Optional[str] = None,
        siparis_id: Optional[int] = None,
    ) -> List[PaletRezervasyonuResponseDTO]:
        kayitlar = self._repo.getir_hepsi(
            skip=skip, limit=limit, durum=durum, siparis_id=siparis_id
        )
        return [PaletRezervasyonuResponseDTO.from_entity(r) for r in kayitlar]


# ─────────────────────────────────────────────────────────────────
# SİPARİŞ REZERVASYONLARI
# ─────────────────────────────────────────────────────────────────

class SiparisRezervasyonlariGetirUseCase:

    def __init__(self, rezervasyon_repo: IPaletRezervasyonuRepository):
        self._repo = rezervasyon_repo

    def execute(self, siparis_id: int) -> List[PaletRezervasyonuResponseDTO]:
        kayitlar = self._repo.getir_siparis_rezervasyonlari(siparis_id)
        return [PaletRezervasyonuResponseDTO.from_entity(r) for r in kayitlar]


# ─────────────────────────────────────────────────────────────────
# REZERVASYON BAŞLAT
# ─────────────────────────────────────────────────────────────────

class RezervasyonBaslatUseCase:
    """
    Sipariş Hazırlanıyor durumuna geçtiğinde çağrılır.

    Her sevkiyat kalemi için FEFO servis aracılığıyla uygun palet seçer
    ve PaletRezervasyonu (Aktif) oluşturur.

    İdempotent: kalem için zaten Aktif rezervasyon varsa skip edilir.
    """

    def __init__(
        self,
        rezervasyon_repo: IPaletRezervasyonuRepository,
        palet_repo: IPaletRepository,
        siparis_repo: ISiparisRepository,
        log_repo: ISistemLogRepository,
        fefo_servisi: Optional[FEFOSecimServisi] = None,
    ):
        self._rezervasyon_repo = rezervasyon_repo
        self._palet_repo = palet_repo
        self._siparis_repo = siparis_repo
        self._log_repo = log_repo
        self._fefo = fefo_servisi or FEFOSecimServisi()

    def execute(
        self,
        siparis_id: int,
        kullanici_id: int,
        auto_commit: bool = True,
    ) -> List[PaletRezervasyonuResponseDTO]:
        siparis = self._siparis_repo.getir_id_ile(siparis_id)
        if not siparis:
            raise KayitBulunamadiError("Sipariş", siparis_id)

        olusturulan: List[PaletRezervasyonu] = []

        for kalem in siparis.kalemler:
            # İdempotency: bu kalem için zaten Aktif rezervasyon var mı?
            mevcut = self._rezervasyon_repo.getir_by_sevkiyat_kalemi(kalem.id or 0)
            if mevcut and mevcut.durum == RezervasyonDurum.AKTIF:
                continue

            # Ürüne ait aktif paletleri kilitleyerek al (FEFO ile sıralanmış).
            # FOR UPDATE: eşzamanlı iki siparişin aynı paleti çifte rezerve etmesini engeller.
            # ÖNEMLİ: Kilit ÖNCE alınır, rezerve_palet_idleri() sonra çağrılır.
            # Ters sırada kilit öncesi okunmuş stale rezerveli_ids, çifte rezervasyona yol açar.
            aktif_paletler = self._palet_repo.getir_fifo_sirayla_kilitli(kalem.urun_id)

            # Kilit alındıktan sonra rezerve edilmiş palet ID'leri okunur — tutarlı snapshot.
            rezerveli_ids = self._rezervasyon_repo.rezerve_palet_idleri(kalem.urun_id)
            uygun_paletler = self._fefo.uygun_ve_siralanmis(aktif_paletler, rezerveli_ids)

            if not uygun_paletler:
                raise YetersizStokError(
                    urun_ismi=f"urun_id={kalem.urun_id} (kalem_id={kalem.id})",
                    mevcut=0,
                    istenen=1,
                )

            palet = uygun_paletler[0]
            rezervasyon = PaletRezervasyonu(
                palet_id=palet.id,
                siparis_id=siparis_id,
                sevkiyat_kalemi_id=kalem.id,
            )
            kaydedilen = self._rezervasyon_repo.olustur(
                rezervasyon,
                auto_commit=auto_commit,
            )
            olusturulan.append(kaydedilen)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.CREATE,
                modul="Palet Rezervasyonu",
                detay=(
                    f"Sipariş #{siparis_id} için {len(olusturulan)} palet rezervasyonu oluşturuldu."
                ),
            ),
            auto_commit=auto_commit,
        )

        return [PaletRezervasyonuResponseDTO.from_entity(r) for r in olusturulan]


# ─────────────────────────────────────────────────────────────────
# REZERVASYON İPTAL (toplu — sipariş iptalinde)
# ─────────────────────────────────────────────────────────────────

class RezervasyonIptalUseCase:
    """Siparişe ait tüm Aktif rezervasyonları iptal eder."""

    def __init__(
        self,
        rezervasyon_repo: IPaletRezervasyonuRepository,
        log_repo: ISistemLogRepository,
    ):
        self._repo = rezervasyon_repo
        self._log_repo = log_repo

    def execute(
        self,
        siparis_id: int,
        kullanici_id: int,
        neden: Optional[str] = None,
        auto_commit: bool = True,
    ) -> int:
        aktif_rezervasyonlar = self._repo.getir_aktif_by_siparis(siparis_id)
        for r in aktif_rezervasyonlar:
            r.iptal_et(neden or "Sipariş iptali")
            self._repo.guncelle(r, auto_commit=auto_commit)

        if aktif_rezervasyonlar:
            self._log_repo.olustur(
                SistemLog.olustur(
                    kullanici_id=kullanici_id,
                    islem_tipi=IslemTipi.UPDATE,
                    modul="Palet Rezervasyonu",
                    detay=(
                        f"Sipariş #{siparis_id} için "
                        f"{len(aktif_rezervasyonlar)} rezervasyon iptal edildi."
                    ),
                ),
                auto_commit=auto_commit,
            )
        return len(aktif_rezervasyonlar)


# ─────────────────────────────────────────────────────────────────
# REZERVASYON KESİNLEŞTİR (toplu — sevkiyat tamamlandığında)
# ─────────────────────────────────────────────────────────────────

class RezervasyonKesinlestirUseCase:
    """Siparişe ait tüm Aktif rezervasyonları Kesinlesti yapar."""

    def __init__(
        self,
        rezervasyon_repo: IPaletRezervasyonuRepository,
        log_repo: ISistemLogRepository,
    ):
        self._repo = rezervasyon_repo
        self._log_repo = log_repo

    def execute(self, siparis_id: int, kullanici_id: int) -> int:
        aktif = self._repo.getir_aktif_by_siparis(siparis_id)
        for r in aktif:
            r.kesinlestir()
            self._repo.guncelle(r)

        if aktif:
            self._log_repo.olustur(
                SistemLog.olustur(
                    kullanici_id=kullanici_id,
                    islem_tipi=IslemTipi.UPDATE,
                    modul="Palet Rezervasyonu",
                    detay=f"Sipariş #{siparis_id} için {len(aktif)} rezervasyon kesinleştirildi.",
                )
            )
        return len(aktif)


# ─────────────────────────────────────────────────────────────────
# REZERVASYON DEĞİŞTİR (admin — farklı palete yeniden rezerve)
# ─────────────────────────────────────────────────────────────────

class RezervasyonDegistirUseCase:
    """Mevcut rezervasyonu iptal edip yeni palet için Aktif rezervasyon oluşturur."""

    def __init__(
        self,
        rezervasyon_repo: IPaletRezervasyonuRepository,
        palet_repo: IPaletRepository,
        log_repo: ISistemLogRepository,
    ):
        self._repo = rezervasyon_repo
        self._palet_repo = palet_repo
        self._log_repo = log_repo

    def execute(
        self,
        rezervasyon_id: int,
        yeni_palet_id: int,
        kullanici_id: int,
        neden: Optional[str] = None,
    ) -> PaletRezervasyonuResponseDTO:
        mevcut = self._repo.getir_id_ile(rezervasyon_id)
        if not mevcut:
            raise KayitBulunamadiError("Rezervasyon", rezervasyon_id)

        if mevcut.durum != RezervasyonDurum.AKTIF:
            raise GecersizIslemError("Yalnızca Aktif rezervasyonlar değiştirilebilir.")

        yeni_palet = self._palet_repo.getir_id_ile(yeni_palet_id)
        if not yeni_palet or not yeni_palet.aktif:
            raise KayitBulunamadiError("Palet", yeni_palet_id)

        # Yeni palete zaten aktif rezervasyon var mı?
        cakisan = self._repo.getir_aktif_by_palet(yeni_palet_id)
        if cakisan:
            raise GecersizIslemError(
                f"Palet #{yeni_palet_id} zaten başka bir siparişe rezerve edilmiş."
            )

        # Mevcut iptal et
        mevcut.iptal_et(neden or "Rezervasyon değiştirildi")
        self._repo.guncelle(mevcut)

        # Yeni oluştur
        yeni = PaletRezervasyonu(
            palet_id=yeni_palet_id,
            siparis_id=mevcut.siparis_id,
            sevkiyat_kalemi_id=mevcut.sevkiyat_kalemi_id,
        )
        kaydedilen = self._repo.olustur(yeni)

        self._log_repo.olustur(
            SistemLog.olustur(
                kullanici_id=kullanici_id,
                islem_tipi=IslemTipi.UPDATE,
                modul="Palet Rezervasyonu",
                detay=(
                    f"Rezervasyon #{rezervasyon_id} değiştirildi: "
                    f"palet #{mevcut.palet_id} → #{yeni_palet_id}. Neden: {neden or '-'}"
                ),
            )
        )

        return PaletRezervasyonuResponseDTO.from_entity(kaydedilen)


# ─────────────────────────────────────────────────────────────────
# STOK DETAY (uygun / rezerve ayrımı)
# ─────────────────────────────────────────────────────────────────

class StokDetayUseCase:
    """Ürün bazlı stok görünürlük özeti: toplam / uygun / rezerve."""

    def __init__(
        self,
        palet_repo: IPaletRepository,
        rezervasyon_repo: IPaletRezervasyonuRepository,
    ):
        self._palet_repo = palet_repo
        self._rezervasyon_repo = rezervasyon_repo

    def execute(self, urun_id: int) -> StokDetayResponseDTO:
        aktif_paletler = self._palet_repo.getir_fifo_sirayla(urun_id)
        toplam_stok = sum(p.koli_adedi for p in aktif_paletler)

        rezerveli_ids = set(self._rezervasyon_repo.rezerve_palet_idleri(urun_id))
        rezerve_stok = sum(
            p.koli_adedi for p in aktif_paletler if p.id in rezerveli_ids
        )
        uygun_stok = toplam_stok - rezerve_stok

        return StokDetayResponseDTO(
            urun_id=urun_id,
            toplam_stok=toplam_stok,
            rezerve_stok=rezerve_stok,
            uygun_stok=max(0, uygun_stok),
        )
