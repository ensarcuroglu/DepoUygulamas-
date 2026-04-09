from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List


class IstisnaKalemTip:
    EKSIK = "Eksik"
    FAZLA = "Fazla"
    HASARLI = "Hasarlı"
    YANLIS_URUN = "YanlışÜrün"
    OKUNAMAZ_BARKOD = "OkunamamazBarkod"
    DIGER = "Diğer"

    _TIPLER = {EKSIK, FAZLA, HASARLI, YANLIS_URUN, OKUNAMAZ_BARKOD, DIGER}

    @classmethod
    def gecerli_mi(cls, tip: str) -> bool:
        return tip in cls._TIPLER


class MalKabulDurum:
    TASLAK = "Taslak"
    ONAYLANDI = "Onaylandi"
    KAPANDI = "Kapandi"

    # Kullanıcı yalnızca ONAYLANDI geçişini tetikleyebilir.
    # KAPANDI sisteme özel: tüm yerleştirme görevleri bitince otomatik kapanır.
    _GECISLER = {
        TASLAK: {ONAYLANDI},
        ONAYLANDI: {KAPANDI},
        KAPANDI: set(),
    }

    @classmethod
    def gecis_gecerli_mi(cls, mevcut: str, hedef: str) -> bool:
        return hedef in cls._GECISLER.get(mevcut, set())


class KalemDurum:
    BEKLIYOR = "Bekliyor"
    GIRIS_YAPILDI = "GirisYapildi"


@dataclass
class MalKabulKalemi:
    """Mal kabul irsaliyesi kalemi — her kalem bir palet tanımı."""

    id: Optional[int] = None
    mal_kabul_irsaliyesi_id: Optional[int] = None
    palet_no: str = ""
    urun_id: int = 0
    lot_no: Optional[str] = None
    miktar: int = 0
    raf_id: Optional[int] = None
    durum: str = KalemDurum.BEKLIYOR
    uretim_tarihi: Optional[date] = None
    son_kullanma_tarihi: Optional[date] = None
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)
    istisna_tip: Optional[str] = None
    istisna_aciklama: Optional[str] = None
    gerceklesen_miktar: Optional[int] = None

    # ── İş Kuralları ──

    def giris_yapildi(self) -> None:
        """Kalemi giriş yapıldı olarak işaretler."""
        if self.durum != KalemDurum.BEKLIYOR:
            raise ValueError("Sadece 'Bekliyor' durumundaki kalemler için giriş yapılabilir.")
        self.durum = KalemDurum.GIRIS_YAPILDI

    def giris_bekliyor_mu(self) -> bool:
        return self.durum == KalemDurum.BEKLIYOR

    def istisna_bildir(
        self,
        tip: str,
        aciklama: Optional[str] = None,
        gerceklesen_miktar: Optional[int] = None,
    ) -> None:
        if not IstisnaKalemTip.gecerli_mi(tip):
            raise ValueError(
                f"Geçersiz istisna tipi: '{tip}'. "
                f"Geçerli tipler: {IstisnaKalemTip._TIPLER}"
            )
        self.istisna_tip = tip
        self.istisna_aciklama = aciklama
        self.gerceklesen_miktar = gerceklesen_miktar

    def istisna_var_mi(self) -> bool:
        return self.istisna_tip is not None


@dataclass
class MalKabulIrsaliye:
    """Mal kabul irsaliyesi domain entity."""

    id: Optional[int] = None
    irsaliye_no: str = ""
    tedarikci_id: int = 0
    depo_id: int = 0
    tir_plaka: Optional[str] = None
    sofor_adi: Optional[str] = None
    durum: str = MalKabulDurum.TASLAK
    tarih: Optional[date] = None
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)
    guncelleme_tarihi: datetime = field(default_factory=datetime.utcnow)

    kalemler: List[MalKabulKalemi] = field(default_factory=list)

    # ── İş Kuralları ──

    def onayla(self) -> None:
        """İrsaliyeyi onaylar — kalemler artık stok girişine hazır."""
        if not MalKabulDurum.gecis_gecerli_mi(self.durum, MalKabulDurum.ONAYLANDI):
            raise ValueError(
                f"Geçersiz durum geçişi: {self.durum} → {MalKabulDurum.ONAYLANDI}"
            )
        if not self.kalemler:
            raise ValueError("Kalemsiz irsaliye onaylanamaz.")
        self.durum = MalKabulDurum.ONAYLANDI
        self.guncelleme_tarihi = datetime.utcnow()

    def kapat(self) -> None:
        """Sistem tarafından çağrılır: tüm yerleştirme görevleri tamamlandığında irsaliyeyi kapatır."""
        if not MalKabulDurum.gecis_gecerli_mi(self.durum, MalKabulDurum.KAPANDI):
            raise ValueError(
                f"Geçersiz durum geçişi: {self.durum} → {MalKabulDurum.KAPANDI}"
            )
        self.durum = MalKabulDurum.KAPANDI
        self.guncelleme_tarihi = datetime.utcnow()

    def durum_degistir(self, yeni_durum: str) -> None:
        """Kullanıcı tetiklemeli geçiş — yalnızca Onaylandi izinlidir.
        Kapandi geçişi sistem tarafından kapat() ile yapılır."""
        if yeni_durum == MalKabulDurum.ONAYLANDI:
            self.onayla()
        else:
            raise ValueError(
                f"Geçersiz veya kullanıcıya kapalı hedef durum: '{yeni_durum}'. "
                "Onaylama için /onayla endpointini kullanın."
            )

    def duzenlenebilir_mi(self) -> bool:
        """Sadece taslak irsaliyeler düzenlenebilir."""
        return self.durum == MalKabulDurum.TASLAK

    def kalem_ekle(self, kalem: MalKabulKalemi) -> None:
        """İrsaliyeye yeni kalem ekler."""
        if not self.duzenlenebilir_mi():
            raise ValueError("Sadece taslak durumundaki irsaliyelere kalem eklenebilir.")
        kalem.mal_kabul_irsaliyesi_id = self.id
        self.kalemler.append(kalem)
        self.guncelleme_tarihi = datetime.utcnow()

    def tum_kalemler_girildi_mi(self) -> bool:
        """Tüm kalemler giriş yapıldı mı kontrol eder."""
        return all(not k.giris_bekliyor_mu() for k in self.kalemler)

    def bekleyen_kalem_sayisi(self) -> int:
        return sum(1 for k in self.kalemler if k.giris_bekliyor_mu())

    def istisna_sayisi(self) -> int:
        return sum(1 for k in self.kalemler if k.istisna_var_mi())

    def istisna_var_mi(self) -> bool:
        return any(k.istisna_var_mi() for k in self.kalemler)
