from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Optional


class SevkiyatDurum:
    PLANLANDI = "Planlandi"
    YUKLENIYOR = "Yukleniyor"
    YOLDA = "Yolda"
    TESLIM_EDILDI = "TeslimEdildi"

    _GECISLER = {
        PLANLANDI: {YUKLENIYOR},
        YUKLENIYOR: {YOLDA},
        YOLDA: {TESLIM_EDILDI},
        TESLIM_EDILDI: set(),
    }

    _STOK_CIKARILMIS = {YUKLENIYOR, YOLDA, TESLIM_EDILDI}

    @classmethod
    def gecis_gecerli_mi(cls, mevcut: str, hedef: str) -> bool:
        return hedef in cls._GECISLER.get(mevcut, set())

    @classmethod
    def stok_cikarilmis_mi(cls, durum: str) -> bool:
        return durum in cls._STOK_CIKARILMIS


@dataclass
class SevkiyatKalemi:
    """Sevkiyat kalemi — sipariş kaleminden 1:1 kopyalanır (yüklenen ürün)."""

    id: Optional[int] = None
    sevkiyat_id: Optional[int] = None
    siparis_kalemi_id: int = 0
    urun_id: int = 0
    miktar: int = 0


@dataclass
class SevkiyatPlani:
    """Sevkiyat planı domain entity."""

    id: Optional[int] = None
    siparis_id: int = 0
    tir_plaka: Optional[str] = None
    sofor_adi: Optional[str] = None
    sofor_telefon: Optional[str] = None
    depo_kapi: Optional[str] = None
    yukleme_tarihi: Optional[date] = None
    cikis_saati: Optional[str] = None
    varis_saati: Optional[str] = None
    durum: str = SevkiyatDurum.PLANLANDI
    notlar: str = ""
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)
    guncelleme_tarihi: datetime = field(default_factory=datetime.utcnow)
    kalemler: List[SevkiyatKalemi] = field(default_factory=list)

    # ── İş Kuralları ──

    def durum_ilerlet(self) -> str:
        """Durumu bir sonraki aşamaya ilerletir."""
        siralama = [
            SevkiyatDurum.PLANLANDI,
            SevkiyatDurum.YUKLENIYOR,
            SevkiyatDurum.YOLDA,
            SevkiyatDurum.TESLIM_EDILDI,
        ]
        idx = siralama.index(self.durum)
        if idx >= len(siralama) - 1:
            raise ValueError("Sevkiyat zaten son durumda (TeslimEdildi).")
        self.durum = siralama[idx + 1]
        self.guncelleme_tarihi = datetime.utcnow()
        return self.durum

    def durum_degistir(self, yeni_durum: str) -> None:
        if not SevkiyatDurum.gecis_gecerli_mi(self.durum, yeni_durum):
            raise ValueError(
                f"Geçersiz sevkiyat durum geçişi: {self.durum} → {yeni_durum}"
            )
        self.durum = yeni_durum
        self.guncelleme_tarihi = datetime.utcnow()

    def teslim_edildi_mi(self) -> bool:
        return self.durum == SevkiyatDurum.TESLIM_EDILDI
