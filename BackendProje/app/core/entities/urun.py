from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


class StokDurum:
    YOK = "Stok Yok"
    KRITIK = "Kritik Stok"
    YETERLI = "Yeterli"


class DepolamaTipi:
    KURU = "Kuru"
    SOGUK = "Soguk"
    TEHLIKELI = "Tehlikeli"

    _TIPLER = {KURU, SOGUK, TEHLIKELI}

    @classmethod
    def gecerli_mi(cls, tip: str) -> bool:
        return tip in cls._TIPLER

    @classmethod
    def tipler(cls) -> set:
        return set(cls._TIPLER)


@dataclass
class Urun:
    """Ürün (product) domain entity.

    stok_miktari alanı infrastructure katmanından hesaplanarak set edilir
    (column_property veya servis katmanı tarafından).
    """

    id: Optional[int] = None
    isim: str = ""
    marka_id: Optional[int] = None
    kategori_id: Optional[int] = None
    tedarikci_id: Optional[int] = None
    ean: Optional[str] = None
    barkod: Optional[str] = None
    ic_adet: int = 1
    gramaj: Optional[float] = None
    birim: str = "Adet"
    fiyat: float = 0.0
    min_stok: int = 10
    aciklama: str = ""
    depolama_tipi: str = DepolamaTipi.KURU  # DepolamaTipi: Kuru, Soguk, Tehlikeli
    aktif: bool = True
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)
    guncelleme_tarihi: datetime = field(default_factory=datetime.utcnow)

    # Hesaplanan alan — repository/servis tarafından doldurulur
    stok_miktari: int = 0

    # ── İş Kuralları ──

    @property
    def durum(self) -> str:
        """Stok durumunu hesaplar."""
        if self.stok_miktari <= 0:
            return StokDurum.YOK
        elif self.stok_miktari <= self.min_stok:
            return StokDurum.KRITIK
        return StokDurum.YETERLI

    @property
    def kritik_mi(self) -> bool:
        """Stok seviyesi kritik eşiğin altında mı?"""
        return self.stok_miktari <= self.min_stok

    def fiyat_guncelle(self, yeni_fiyat: float) -> None:
        if yeni_fiyat < 0:
            raise ValueError("Fiyat negatif olamaz.")
        self.fiyat = yeni_fiyat
        self.guncelleme_tarihi = datetime.utcnow()

    def deaktif_et(self) -> None:
        self.aktif = False
        self.guncelleme_tarihi = datetime.utcnow()

    def stok_giris_yapilabilir_mi(self, miktar: int) -> bool:
        """Giriş miktarının geçerli olup olmadığını kontrol eder."""
        return miktar > 0

    def stok_cikis_yapilabilir_mi(self, miktar: int) -> bool:
        """Çıkış miktarının mevcut stoktan karşılanıp karşılanamayacağını kontrol eder."""
        return 0 < miktar <= self.stok_miktari

    def zon_uygun_mu(self, zon_tipi: str) -> bool:
        """Ürünün depolama tipinin verilen zon tipine uygun olup olmadığını kontrol eder."""
        from app.core.entities.zon import ZonTipi  # circular import önlemek için lazy
        return self.depolama_tipi in ZonTipi.izin_verilen_depolama_tipleri(zon_tipi)
