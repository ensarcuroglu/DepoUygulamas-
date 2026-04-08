from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.core.exceptions import GecersizDurumGecisiError


class GorevTipi:
    YERLESTIRME = "Yerlestirme"       # Mal kabul sonrası normal yerleştirme
    TRANSFER = "Transfer"              # Karantina çıkış vb. zon-arası transfer
    BELIRSIZ_KONUM = "BelirsizKonum"  # MIGRATION_STAGING'den yerleştirme

    _TIPLER = {YERLESTIRME, TRANSFER, BELIRSIZ_KONUM}

    @classmethod
    def gecerli_mi(cls, tip: str) -> bool:
        return tip in cls._TIPLER


class GorevDurum:
    BEKLIYOR = "Bekliyor"         # Sistem oluşturdu, havuzda bekliyor
    ATANDI = "Atandi"             # Operatör çekti (kilitli)
    DEVAM_EDIYOR = "DevamEdiyor"  # Operatör paleti aldı
    TAMAMLANDI = "Tamamlandi"     # Raf okutuldu, doğrulandı, yerleştirildi
    IPTAL_EDILDI = "IptalEdildi"  # İptal (raf değişikliği, stok iadesi vb.)

    _GECISLER: dict[str, set[str]] = {}  # sınıf yüklendikten sonra doldurulur

    @classmethod
    def gecis_gecerli_mi(cls, mevcut: str, hedef: str) -> bool:
        return hedef in cls._GECISLER.get(mevcut, set())


# Durum geçiş tablosu — değerler tanımlandıktan sonra kurulur
GorevDurum._GECISLER = {
    GorevDurum.BEKLIYOR: {GorevDurum.ATANDI, GorevDurum.IPTAL_EDILDI},
    GorevDurum.ATANDI: {
        GorevDurum.DEVAM_EDIYOR,
        GorevDurum.BEKLIYOR,   # bırak (operatör görevi iade eder)
        GorevDurum.IPTAL_EDILDI,
    },
    GorevDurum.DEVAM_EDIYOR: {GorevDurum.TAMAMLANDI, GorevDurum.IPTAL_EDILDI},
    GorevDurum.TAMAMLANDI: set(),
    GorevDurum.IPTAL_EDILDI: set(),
}


@dataclass
class YerlestirmeGorevi:
    """Yerleştirme (Putaway) görev domain entity."""

    id: Optional[int] = None
    palet_id: int = 0
    mal_kabul_irsaliye_id: Optional[int] = None
    depo_id: Optional[int] = None
    tip: str = GorevTipi.YERLESTIRME
    kaynak_raf_id: Optional[int] = None        # Transfer görevlerinde: şu anki raf
    onerilen_raf_id: int = 0                   # Algoritmanın önerdiği hedef raf
    gerceklesen_raf_id: Optional[int] = None   # Operatörün fiilen yerleştirdiği raf
    durum: str = GorevDurum.BEKLIYOR
    oncelik: int = 5                           # 1=Acil … 5=Normal
    atanan_kullanici_id: Optional[int] = None
    override_kullanici_id: Optional[int] = None
    override_neden: Optional[str] = None
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)
    atanma_tarihi: Optional[datetime] = None    # Operatörün görevi havuzdan çektiği an (timeout için)
    baslama_tarihi: Optional[datetime] = None   # Operatörün paleti fiziksel olarak aldığı an
    tamamlanma_tarihi: Optional[datetime] = None
    iptal_nedeni: Optional[str] = None

    # ── İş Kuralları ──

    def _durum_gecisi(self, hedef: str) -> None:
        if not GorevDurum.gecis_gecerli_mi(self.durum, hedef):
            raise GecersizDurumGecisiError(
                f"Geçersiz durum geçişi: {self.durum} → {hedef}",
                mevcut=self.durum,
                hedef=hedef
            )
        self.durum = hedef

    def ata(self, kullanici_id: int) -> None:
        """Operatör görevi havuzdan çeker (pull-based FIFO)."""
        self._durum_gecisi(GorevDurum.ATANDI)
        self.atanan_kullanici_id = kullanici_id
        self.atanma_tarihi = datetime.utcnow()

    def baslat(self) -> None:
        """Operatör paleti fiziksel olarak aldı."""
        self._durum_gecisi(GorevDurum.DEVAM_EDIYOR)
        self.baslama_tarihi = datetime.utcnow()

    def bırak(self) -> None:
        """Operatör görevi havuza iade eder."""
        self._durum_gecisi(GorevDurum.BEKLIYOR)
        self.atanan_kullanici_id = None
        self.atanma_tarihi = None

    def zaman_asimina_ugradi(self, timeout_dk: int) -> bool:
        """Görev atanma süresini aştı mı? (timeout_dk dakika)"""
        if self.durum != GorevDurum.ATANDI or self.atanma_tarihi is None:
            return False
        gecen = (datetime.utcnow() - self.atanma_tarihi).total_seconds() / 60
        return gecen >= timeout_dk

    def tamamla(self, gerceklesen_raf_id: int) -> None:
        """Raf okutuldu, fiziksel yerleştirme onaylandı."""
        self._durum_gecisi(GorevDurum.TAMAMLANDI)
        self.gerceklesen_raf_id = gerceklesen_raf_id
        self.tamamlanma_tarihi = datetime.utcnow()

    def override_ile_tamamla(
        self, gerceklesen_raf_id: int, supervisor_id: int, neden: str
    ) -> None:
        """Süpervizör override ile tamamlar (kapasite/zon kuralı ihlali)."""
        self._durum_gecisi(GorevDurum.TAMAMLANDI)
        self.gerceklesen_raf_id = gerceklesen_raf_id
        self.override_kullanici_id = supervisor_id
        self.override_neden = neden
        self.tamamlanma_tarihi = datetime.utcnow()

    def iptal_et(self, neden: str) -> None:
        self._durum_gecisi(GorevDurum.IPTAL_EDILDI)
        self.iptal_nedeni = neden

    def onerilen_raf_farkli_mi(self) -> bool:
        """Operatör algoritmanın önerdiğinden farklı bir rafa mı yerleştirdi?"""
        return (
            self.gerceklesen_raf_id is not None
            and self.gerceklesen_raf_id != self.onerilen_raf_id
        )
