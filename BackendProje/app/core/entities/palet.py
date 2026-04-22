from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional

from app.core.exceptions import GecersizDurumGecisiError, GecersizIslemError


# ── Üretim Paleti State Machine ──

class UretimPaletDurum:
    """Üretim paleti yaşam döngüsü state machine."""
    OLUSTURULDU = "Olusturuldu"
    KABUL_BEKLIYOR = "KabulBekliyor"
    KABUL_EDILDI = "KabulEdildi"
    YERLESTIRME_BEKLIYOR = "YerlestirmeBekliyor"
    YERLESTIRILDI = "Yerlestirildi"
    IPTAL_EDILDI = "IptalEdildi"
    KARANTINA = "Karantina"

    # Stok etkisi kümeleri
    STOKTA_DURUMLAR = {KABUL_EDILDI, YERLESTIRILDI, KARANTINA}
    KULLANILABILIR_DURUMLAR = {KABUL_EDILDI, YERLESTIRILDI}

    _GECISLER: dict[str, set[str]] = {}

    @classmethod
    def gecis_gecerli_mi(cls, mevcut: str, hedef: str) -> bool:
        return hedef in cls._GECISLER.get(mevcut, set())


UretimPaletDurum._GECISLER = {
    UretimPaletDurum.OLUSTURULDU: {
        UretimPaletDurum.KABUL_BEKLIYOR,
        UretimPaletDurum.IPTAL_EDILDI,
    },
    UretimPaletDurum.KABUL_BEKLIYOR: {
        UretimPaletDurum.KABUL_EDILDI,
        UretimPaletDurum.IPTAL_EDILDI,
    },
    UretimPaletDurum.KABUL_EDILDI: {
        UretimPaletDurum.YERLESTIRME_BEKLIYOR,
        UretimPaletDurum.KARANTINA,
    },
    UretimPaletDurum.YERLESTIRME_BEKLIYOR: {
        UretimPaletDurum.YERLESTIRILDI,
    },
    UretimPaletDurum.YERLESTIRILDI: set(),
    UretimPaletDurum.IPTAL_EDILDI: set(),
    UretimPaletDurum.KARANTINA: {
        UretimPaletDurum.KABUL_EDILDI,
    },
}


# ── Hafif nested bilgi yapıları (DTO zenginleştirme amaçlı) ──

@dataclass
class UrunBilgi:
    """Palet yanıtında taşınan minimal ürün bilgisi."""
    id: Optional[int] = None
    isim: str = ""
    ean: Optional[str] = None
    barkod: Optional[str] = None


@dataclass
class LotBilgi:
    """Palet yanıtında taşınan minimal lot bilgisi."""
    id: Optional[int] = None
    lot_no: Optional[str] = None
    urun_id: int = 0
    uretim_tarihi: Optional[date] = None
    son_kullanma_tarihi: Optional[date] = None
    urun: Optional[UrunBilgi] = None


@dataclass
class RafBilgi:
    """Palet yanıtında taşınan minimal raf bilgisi."""
    id: Optional[int] = None
    kod: str = ""
    bolge: str = ""


@dataclass
class Palet:
    """Palet domain entity."""

    id: Optional[int] = None
    lot_id: int = 0
    raf_id: int = 0  # migrate_putaway_system.py Adım 10 sonrası zorunlu
    palet_no: str = ""
    koli_adedi: int = 0
    palet_kg: Optional[float] = None
    vardiya: Optional[str] = None
    tarih: datetime = field(default_factory=datetime.utcnow)
    aktif: bool = True
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)

    # ── Üretim paleti alanları (None = legacy palet) ──
    kaynak: Optional[str] = None
    durum: Optional[str] = None
    uretim_tarihi: Optional[date] = None
    lot_no: Optional[str] = None

    # ── Kabul audit alanları ──
    kabul_eden_kullanici_id: Optional[int] = None
    kabul_tarihi: Optional[datetime] = None
    iptal_sebebi: Optional[str] = None

    # ── Üretim meta alanları (opsiyonel; endüstri standardı izlenebilirlik) ──
    uretim_hatti: Optional[str] = None
    makine_kodu: Optional[str] = None
    operator_kullanici_id: Optional[int] = None
    brut_kg: Optional[float] = None
    net_kg: Optional[float] = None

    # Opsiyonel nested bilgi — mapper tarafından doldurulur
    lot: Optional[LotBilgi] = None
    raf: Optional[RafBilgi] = None

    # ── İş Kuralları ──

    def stok_dus(self, miktar: int) -> int:
        """Paletten belirtilen miktarda koli düşer.

        Returns:
            Düşürülen gerçek miktar (palet koli_adedi < miktar ise tamamını düşer).
        """
        if miktar <= 0:
            raise ValueError("Düşülecek miktar pozitif olmalı.")

        if self.koli_adedi <= miktar:
            dusurulen = self.koli_adedi
            self.koli_adedi = 0
            self.aktif = False
            return dusurulen
        else:
            self.koli_adedi -= miktar
            return miktar

    def sevk_et(self) -> None:
        """Paletin tamamını sevk eder (deaktif eder)."""
        self.koli_adedi = 0
        self.aktif = False

    def bos_mu(self) -> bool:
        return self.koli_adedi <= 0

    def raf_ata(self, raf_id: int) -> None:
        """Paleti bir rafa atar."""
        self.raf_id = raf_id

    # ── Üretim Paleti İş Kuralları ──

    @property
    def uretim_paleti_mi(self) -> bool:
        """Bu palet üretim kaynaklı mı?"""
        return self.kaynak == "uretim" and self.durum is not None

    def _uretim_durum_gecisi(self, hedef: str) -> None:
        """Üretim paleti durum geçişi — iç yardımcı."""
        if not self.uretim_paleti_mi:
            raise GecersizIslemError(
                "Bu palet için durum geçişi uygulanamaz (üretim paleti değil)."
            )
        if not UretimPaletDurum.gecis_gecerli_mi(self.durum, hedef):
            raise GecersizDurumGecisiError("Palet", mevcut=self.durum, hedef=hedef)
        self.durum = hedef

    def kabul_bekle(self) -> None:
        """OLUSTURULDU → KABUL_BEKLIYOR"""
        self._uretim_durum_gecisi(UretimPaletDurum.KABUL_BEKLIYOR)

    def kabul_et(self, kullanici_id: int) -> None:
        """KABUL_BEKLIYOR → KABUL_EDILDI (stok artışı tetiklenir)."""
        if self.durum == UretimPaletDurum.KABUL_EDILDI:
            raise GecersizIslemError("Bu palet zaten kabul edilmiş.")
        if self.durum == UretimPaletDurum.IPTAL_EDILDI:
            raise GecersizIslemError(
                "İptal edilmiş palet kabul edilemez; yeniden etiket gerekir."
            )
        self._uretim_durum_gecisi(UretimPaletDurum.KABUL_EDILDI)
        self.kabul_eden_kullanici_id = kullanici_id
        self.kabul_tarihi = datetime.utcnow()

    def yerlestirme_bekle(self) -> None:
        """KABUL_EDILDI → YERLESTIRME_BEKLIYOR"""
        self._uretim_durum_gecisi(UretimPaletDurum.YERLESTIRME_BEKLIYOR)

    def yerlestir(self, raf_id: int) -> None:
        """YERLESTIRME_BEKLIYOR → YERLESTIRILDI"""
        self._uretim_durum_gecisi(UretimPaletDurum.YERLESTIRILDI)
        self.raf_id = raf_id

    def karantinaya_al(self) -> None:
        """KABUL_EDILDI → KARANTINA"""
        self._uretim_durum_gecisi(UretimPaletDurum.KARANTINA)

    def karantinadan_cikar(self) -> None:
        """KARANTINA → KABUL_EDILDI (yetkili onayı use case'de kontrol edilir)."""
        self._uretim_durum_gecisi(UretimPaletDurum.KABUL_EDILDI)

    def iptal_et(self, sebep: str) -> None:
        """OLUSTURULDU/KABUL_BEKLIYOR → IPTAL_EDILDI"""
        self._uretim_durum_gecisi(UretimPaletDurum.IPTAL_EDILDI)
        self.iptal_sebebi = sebep
        self.aktif = False

    # ── Stok Etkisi Sorguları ──

    @property
    def stokta_mi(self) -> bool:
        """Legacy: aktif ise stokta. Üretim: durum bazlı."""
        if not self.uretim_paleti_mi:
            return self.aktif
        return self.durum in UretimPaletDurum.STOKTA_DURUMLAR

    @property
    def kullanilabilir_mi(self) -> bool:
        """Sevk/toplama için kullanılabilir mi?"""
        if not self.uretim_paleti_mi:
            return self.aktif
        return self.durum in UretimPaletDurum.KULLANILABILIR_DURUMLAR
