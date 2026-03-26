from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List


class MalKabulDurum:
    TASLAK = "Taslak"
    ONAYLANDI = "Onaylandi"
    TAMAMLANDI = "Tamamlandi"

    _GECISLER = {
        TASLAK: {ONAYLANDI},
        ONAYLANDI: {TAMAMLANDI},
        TAMAMLANDI: set(),
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

    # ── İş Kuralları ──

    def giris_yapildi(self) -> None:
        """Kalemi giriş yapıldı olarak işaretler."""
        if self.durum != KalemDurum.BEKLIYOR:
            raise ValueError("Sadece 'Bekliyor' durumundaki kalemler için giriş yapılabilir.")
        self.durum = KalemDurum.GIRIS_YAPILDI

    def giris_bekliyor_mu(self) -> bool:
        return self.durum == KalemDurum.BEKLIYOR


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

    def tamamla(self) -> None:
        """Tüm kalemler giriş yapıldıysa irsaliyeyi tamamlar."""
        if not MalKabulDurum.gecis_gecerli_mi(self.durum, MalKabulDurum.TAMAMLANDI):
            raise ValueError(
                f"Geçersiz durum geçişi: {self.durum} → {MalKabulDurum.TAMAMLANDI}"
            )
        bekleyen = [k for k in self.kalemler if k.giris_bekliyor_mu()]
        if bekleyen:
            raise ValueError(
                f"{len(bekleyen)} kalem henüz giriş yapılmamış. Tamamlamak için tüm kalemler girilmelidir."
            )
        self.durum = MalKabulDurum.TAMAMLANDI
        self.guncelleme_tarihi = datetime.utcnow()

    def durum_degistir(self, yeni_durum: str) -> None:
        """Genel durum geçiş yönlendiricisi."""
        if yeni_durum == MalKabulDurum.ONAYLANDI:
            self.onayla()
        elif yeni_durum == MalKabulDurum.TAMAMLANDI:
            self.tamamla()
        else:
            raise ValueError(f"Geçersiz hedef durum: {yeni_durum}")

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
