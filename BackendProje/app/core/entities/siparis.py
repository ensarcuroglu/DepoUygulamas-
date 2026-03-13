from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List


class SiparisDurum:
    BEKLEME = "Bekleme"
    HAZIRLANIYOR = "Hazirlaniyor"
    YOLA_CIKTI = "YolaCikti"
    TESLIM_EDILDI = "TeslimEdildi"
    IPTAL = "Iptal"

    # Geçerli durum geçişleri
    _GECISLER = {
        BEKLEME: {HAZIRLANIYOR, IPTAL},
        HAZIRLANIYOR: {YOLA_CIKTI, IPTAL},
        YOLA_CIKTI: {TESLIM_EDILDI},
        TESLIM_EDILDI: set(),
        IPTAL: set(),
    }

    @classmethod
    def gecis_gecerli_mi(cls, mevcut: str, hedef: str) -> bool:
        return hedef in cls._GECISLER.get(mevcut, set())


@dataclass
class SiparisKalemi:
    """Sipariş kalemi domain entity."""

    id: Optional[int] = None
    siparis_id: Optional[int] = None
    urun_id: int = 0
    miktar: int = 0
    birim_fiyat: float = 0.0
    kdv_orani: float = 18.0
    toplam: float = 0.0

    def toplam_hesapla(self) -> float:
        """KDV dahil toplamı hesaplar."""
        self.toplam = self.miktar * self.birim_fiyat * (1 + self.kdv_orani / 100)
        return self.toplam


@dataclass
class Siparis:
    """Sipariş domain entity."""

    id: Optional[int] = None
    siparis_no: str = ""
    musteri_adi: str = ""
    teslimat_adresi: str = ""
    teslimat_tarihi: Optional[date] = None
    durum: str = SiparisDurum.BEKLEME
    top_miktar: int = 0
    top_tutar: float = 0.0
    notlar: str = ""
    olusturan_kullanici_id: Optional[int] = None
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)
    guncelleme_tarihi: datetime = field(default_factory=datetime.utcnow)
    aktif: bool = True

    kalemler: List[SiparisKalemi] = field(default_factory=list)

    # ── İş Kuralları ──

    def durum_degistir(self, yeni_durum: str) -> None:
        """Durum geçişini iş kuralına göre doğrular ve uygular."""
        if not SiparisDurum.gecis_gecerli_mi(self.durum, yeni_durum):
            raise ValueError(
                f"Geçersiz durum geçişi: {self.durum} → {yeni_durum}"
            )
        self.durum = yeni_durum
        self.guncelleme_tarihi = datetime.utcnow()

    def iptal_et(self) -> None:
        """Siparişi iptal eder."""
        self.durum_degistir(SiparisDurum.IPTAL)

    def toplam_hesapla(self) -> None:
        """Kalemlerden toplam miktar ve tutarı hesaplar."""
        self.top_miktar = sum(k.miktar for k in self.kalemler)
        self.top_tutar = sum(k.toplam for k in self.kalemler)
        self.guncelleme_tarihi = datetime.utcnow()

    def kalem_ekle(self, kalem: SiparisKalemi) -> None:
        """Siparişe yeni kalem ekler ve toplamları günceller."""
        kalem.toplam_hesapla()
        self.kalemler.append(kalem)
        self.toplam_hesapla()

    def iptal_edilebilir_mi(self) -> bool:
        return SiparisDurum.gecis_gecerli_mi(self.durum, SiparisDurum.IPTAL)
