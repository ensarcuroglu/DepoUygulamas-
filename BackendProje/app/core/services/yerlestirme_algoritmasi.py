"""
Yerleştirme Algoritması — WMS endüstri standardı putaway algorithm.

Karar hiyerarşisi:
  1. Uygunluk  : Ürün depolama tipi ⊂ Zon izin verilen tipler
                 (kalıcı depolama olmayan zonlar — MalKabul, Sevkiyat,
                  Karantina — burada elenir; tek noktada
                  ZonUyumlulukServisi tarafından yapılır.)
  2. Kapasite  : Raf slot + ağırlık kapasitesi yeterli mi
  3. Verimlilik (varsayılan ağırlıklar):
     a) Konsolidasyon  (%40) — Aynı ürün rafında toplanma; karışık SKU
        rafına ceza, farklı tek-SKU rafına caydırıcı düşük puan.
     b) Doluluk        (%30) — U-eğrisi: %85'e kadar artar, %85+ rafta
        palet erişim sıkışmasını önlemek için ceza.
     c) FIFO uyumu     (%20) — SKT'si yakın paletlerin bir arada tutulması
        (aslen "skt_uyumu"; DTO key'i geriye uyumluluk için "fifo").
     d) Zon önceliği   (%10) — Tercih edilen zon sırası (yapılandırılabilir)

Performans:
  Aday raflar belirlendikten sonra tüm rafların paletleri ve zonları tek
  seferde toplu olarak yüklenir; skorlama metodları DB'ye gitmez.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

from app.core.entities.raf import Raf
from app.core.entities.palet import Palet
from app.core.entities.urun import Urun
from app.core.entities.zon import Zon
from app.core.repositories.raf_repository import IRafRepository
from app.core.repositories.zon_repository import IZonRepository
from app.core.repositories.palet_repository import IPaletRepository
from app.core.services.zon_uyumluluk_servisi import ZonUyumlulukServisi
from app.core.services.kapasite_dogrulama_servisi import KapasiteDogrulamaServisi


# ── Varsayılan zon tercih öncelikleri (düşük = daha önce değerlendirilir) ──
_VARSAYILAN_ZON_TIPI_TERCIH: Dict[str, int] = {
    "Genel": 1,
    "Soguk": 1,
    "Tehlikeli": 1,
    "MalKabul": 5,    # Staging — algoritma normalde buraya önermez (filtrede elenir)
    "Sevkiyat": 5,
    "Karantina": 10,
}
_ZON_ONCELIK_VARSAYILAN = 3


@dataclass(frozen=True)
class YerlestirmeAyarlari:
    """Algoritma ağırlıkları ve zon tercih konfigürasyonu.

    Constructor'da default ile alınır; depo bazında özelleştirme
    gerektiğinde DI'da farklı bir instance enjekte edilir.
    """
    konsolidasyon_agirlik: float = 0.40
    doluluk_agirlik: float = 0.30
    fifo_agirlik: float = 0.20
    zon_oncelik_agirlik: float = 0.10
    zon_tercih: Dict[str, int] = field(default_factory=lambda: dict(_VARSAYILAN_ZON_TIPI_TERCIH))
    raf_aday_limiti: int = 1000          # Zon başına aday raf üst sınırı
    doluluk_doyma_orani: float = 0.85    # Bu oranda doluluk = max skor; üstü cezalandırılır
    fifo_tolerans_gun: int = 30          # Bu fark üstü FIFO skoru 0
    alternatif_sayisi: int = 3

    def agirliklar(self) -> Dict[str, float]:
        return {
            "konsolidasyon": self.konsolidasyon_agirlik,
            "doluluk": self.doluluk_agirlik,
            "fifo": self.fifo_agirlik,
            "zon_oncelik": self.zon_oncelik_agirlik,
        }


@dataclass
class AlternatifOneri:
    """Alternatif raf için skor + bileşen + gerekçe taşır."""
    raf: Raf
    skor: float
    bilesenler: Dict[str, float] = field(default_factory=dict)
    gerekce: str = ""


@dataclass
class YerlestirmeOnerisi:
    """Yerleştirme algoritmasının ürettiği öneri."""
    onerilen_raf: Raf
    skor: float                         # 0–100
    alternatifler: List[Raf] = field(default_factory=list)  # Geri uyumluluk
    gerekce: str = ""
    bilesenler: Dict[str, float] = field(default_factory=dict)
    alternatif_detaylari: List[AlternatifOneri] = field(default_factory=list)
    agirliklar: Dict[str, float] = field(default_factory=dict)


class YerlestirmeAlgoritmasi:
    """
    Palet için en uygun rafı önerir.

    Domain servisi — saf hesaplama + read-only repository erişimi.
    Yazma yapmaz.
    """

    def __init__(
        self,
        raf_repo: IRafRepository,
        zon_repo: IZonRepository,
        palet_repo: IPaletRepository,
        zon_uyumluluk: ZonUyumlulukServisi,
        kapasite_dogrulama: KapasiteDogrulamaServisi,
        ayarlar: Optional[YerlestirmeAyarlari] = None,
    ):
        self._raf_repo = raf_repo
        self._zon_repo = zon_repo
        self._palet_repo = palet_repo
        self._zon_uyumluluk = zon_uyumluluk
        self._kapasite = kapasite_dogrulama
        self._ayarlar = ayarlar or YerlestirmeAyarlari()

    # ─────────────────────────────────────────────────────────────────────────
    # Ana API
    # ─────────────────────────────────────────────────────────────────────────

    def raf_oner(self, palet: Palet, urun: Urun, depo_id: int) -> Optional[YerlestirmeOnerisi]:
        """Palet için en uygun rafı önerir; uygun raf yoksa None."""
        palet_kg = palet.palet_kg or 0.0

        # 1. Kalıcı depolama için uygun zonlar
        uygun_zonlar = self._zon_uyumluluk.uyumlu_zonlari_getir(
            depo_id, urun.depolama_tipi, sadece_kalici_depolama=True
        )
        if not uygun_zonlar:
            return None

        # 2. Aday raflar
        adaylar: List[Raf] = []
        for zon in uygun_zonlar:
            raflar = self._raf_repo.getir_hepsi(
                zon_id=zon.id,
                sadece_aktif=True,
                limit=self._ayarlar.raf_aday_limiti,
            )
            adaylar.extend(raflar)

        if not adaylar:
            return None

        # 3. Pre-fetch: tüm aday rafların paletleri tek sorguda
        raf_ids = [r.id for r in adaylar if r.id is not None]
        palet_haritasi = self._palet_haritasi_olustur(raf_ids)

        # Zon haritası — _zon_onceligi_skoru için tek seferde yükle
        zon_haritasi: Dict[int, Zon] = {z.id: z for z in uygun_zonlar if z.id is not None}

        # 4. Kapasite filtresi (ön-yüklenen palet listeleriyle)
        uygun_raflar: List[Raf] = []
        for raf in adaylar:
            mevcut = palet_haritasi.get(raf.id, [])
            if self._kapasite_yeterli_mi(raf, mevcut, palet_kg):
                uygun_raflar.append(raf)

        if not uygun_raflar:
            return None

        # 5. Skorlama
        skorlar = []
        for raf in uygun_raflar:
            mevcut = palet_haritasi.get(raf.id, [])
            zon = zon_haritasi.get(raf.zon_id) if raf.zon_id else None
            skor, bilesenler = self._skor_ve_bilesenler(raf, urun, palet, mevcut, zon)
            skorlar.append((raf, skor, bilesenler, mevcut))

        # Tie-break: skor desc → raf.kod asc → raf.id asc (deterministik)
        skorlar.sort(key=lambda x: (-x[1], x[0].kod or "", x[0].id or 0))

        en_iyi_raf, en_iyi_skor, en_iyi_bilesenler, en_iyi_mevcut = skorlar[0]
        alt_n = self._ayarlar.alternatif_sayisi
        alternatif_detaylari = [
            AlternatifOneri(
                raf=r,
                skor=round(s, 1),
                bilesenler=b,
                gerekce=self._gerekce_olustur(r, urun, s, m),
            )
            for r, s, b, m in skorlar[1:1 + alt_n]
        ]

        return YerlestirmeOnerisi(
            onerilen_raf=en_iyi_raf,
            skor=round(en_iyi_skor, 1),
            alternatifler=[a.raf for a in alternatif_detaylari],
            gerekce=self._gerekce_olustur(en_iyi_raf, urun, en_iyi_skor, en_iyi_mevcut),
            bilesenler=en_iyi_bilesenler,
            alternatif_detaylari=alternatif_detaylari,
            agirliklar=self._ayarlar.agirliklar(),
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Pre-fetch yardımcıları
    # ─────────────────────────────────────────────────────────────────────────

    def _palet_haritasi_olustur(self, raf_ids: List[int]) -> Dict[int, List[Palet]]:
        """raf_id → aktif palet listesi haritasını tek sorguda çıkarır."""
        if not raf_ids:
            return {}
        # Tek batch ile tüm aktif paletleri getir (limit'i aday sayısı*makul kapasite ile sınırla)
        tahmini_limit = max(500, len(raf_ids) * 100)
        paletler = self._palet_repo.getir_hepsi(
            raf_ids=raf_ids,
            sadece_aktif=True,
            limit=tahmini_limit,
        )
        harita: Dict[int, List[Palet]] = {rid: [] for rid in raf_ids}
        for p in paletler:
            if p.raf_id in harita:
                harita[p.raf_id].append(p)
        return harita

    def _kapasite_yeterli_mi(self, raf: Raf, mevcut: List[Palet], yeni_palet_kg: float) -> bool:
        """Önceden çekilmiş palet listesiyle kapasite kontrolü (DB'ye gitmez)."""
        mevcut_adet = len(mevcut)
        mevcut_agirlik = sum(p.palet_kg or 0.0 for p in mevcut)
        sonuc = raf.kapasite_yeterli_mi(mevcut_adet, mevcut_agirlik, yeni_palet_kg)
        return sonuc.yeterli

    # ─────────────────────────────────────────────────────────────────────────
    # Skorlama
    # ─────────────────────────────────────────────────────────────────────────

    def _skorla(self, raf: Raf, urun: Urun, palet: Palet) -> float:
        """Geri uyumluluk: tek raf için skor (DB'den palet ve zon çekerek)."""
        skor, _ = self._skor_ve_bilesenler(raf, urun, palet)
        return skor

    def _skor_ve_bilesenler(
        self,
        raf: Raf,
        urun: Urun,
        palet: Palet,
        mevcut_paletler: Optional[List[Palet]] = None,
        zon: Optional[Zon] = None,
    ) -> tuple[float, Dict[str, float]]:
        """Bileşik skor + ham bileşen sözlüğü (açıklanabilirlik için)."""
        if mevcut_paletler is None:
            mevcut_paletler = self._palet_repo.getir_hepsi(
                raf_id=raf.id, sadece_aktif=True, limit=200
            )
        if zon is None and raf.zon_id:
            zon = self._zon_repo.getir_id_ile(raf.zon_id)

        konsolidasyon = self._konsolidasyon_skoru(urun, mevcut_paletler)
        doluluk = self._doluluk_skoru(raf, mevcut_paletler)
        fifo = self._fifo_skoru(palet, mevcut_paletler)
        zon_oncelik = self._zon_onceligi_skoru(zon)

        a = self._ayarlar
        skor = (
            konsolidasyon * a.konsolidasyon_agirlik
            + doluluk * a.doluluk_agirlik
            + fifo * a.fifo_agirlik
            + zon_oncelik * a.zon_oncelik_agirlik
        )
        bilesenler = {
            "konsolidasyon": round(konsolidasyon, 1),
            "doluluk": round(doluluk, 1),
            "fifo": round(fifo, 1),
            "zon_oncelik": round(zon_oncelik, 1),
        }
        return skor, bilesenler

    def _konsolidasyon_skoru(self, urun: Urun, mevcut_paletler: List[Palet]) -> float:
        """SKU homojenliği skoru (0–100):
          - Boş raf: 50 (nötr — yeni başlangıç)
          - Aynı tek SKU: 40 + 12·sqrt(adet), max 100
          - Farklı tek SKU: 10 (caydırıcı, ama eleyici değil)
          - Karışık raf (2+ farklı SKU): 0
        """
        if not mevcut_paletler:
            return 50.0

        # Mevcut paletlerden distinct urun_id seti
        urun_idleri = {
            p.lot.urun_id for p in mevcut_paletler if p.lot and p.lot.urun_id
        }
        if not urun_idleri:
            return 50.0  # Lot/ürün ilişkisi tespit edilemiyor — nötr

        if len(urun_idleri) >= 2:
            return 0.0  # Karışık raf

        (tek_urun_id,) = urun_idleri
        if tek_urun_id == urun.id:
            ayni_urun = sum(
                1 for p in mevcut_paletler
                if p.lot and p.lot.urun_id == urun.id
            )
            return min(40.0 + 12.0 * math.sqrt(ayni_urun), 100.0)
        return 10.0

    def _doluluk_skoru(self, raf: Raf, mevcut_paletler: List[Palet]) -> float:
        """U-eğrisi: doyma_orani'na kadar artar, sonra hızla düşer (0–100)."""
        if raf.kapasite <= 0:
            return 0.0
        oran = min(len(mevcut_paletler) / raf.kapasite, 1.0)
        doyma = self._ayarlar.doluluk_doyma_orani
        if oran <= doyma:
            return (oran / doyma) * 100.0 if doyma > 0 else 100.0
        kalan = 1.0 - doyma
        if kalan <= 0:
            return 100.0
        return max(0.0, 100.0 - ((oran - doyma) / kalan) * 100.0)

    def _fifo_skoru(self, palet: Palet, mevcut_paletler: List[Palet]) -> float:
        """SKT uyumu (0–100). Ad geriye uyumluluk için 'fifo' bilesen key'i."""
        palet_skt = palet.lot.son_kullanma_tarihi if palet.lot else None
        if not palet_skt:
            return 50.0  # SKT bilgisi yoksa nötr

        skt_listesi = [
            p.lot.son_kullanma_tarihi
            for p in mevcut_paletler
            if p.lot and p.lot.son_kullanma_tarihi
        ]
        if not skt_listesi:
            return 50.0  # Boş raf veya SKT'siz — nötr

        en_erken_skt: date = min(skt_listesi)
        fark_gun = abs((palet_skt - en_erken_skt).days)
        tolerans = max(1, self._ayarlar.fifo_tolerans_gun)
        return max(0.0, 100.0 - fark_gun * (100.0 / tolerans))

    def _zon_onceligi_skoru(self, zon: Optional[Zon]) -> float:
        """Tercih edilen zonlar daha yüksek skor (0–100)."""
        if not zon:
            return 50.0
        tercih = self._ayarlar.zon_tercih.get(zon.tip, _ZON_ONCELIK_VARSAYILAN)
        # tercih 1 (en iyi) → 100, tercih 10 (en kötü) → 0
        return max(0.0, 100.0 - (tercih - 1) * (100.0 / 9.0))

    # ─────────────────────────────────────────────────────────────────────────
    # Gerekçe metni
    # ─────────────────────────────────────────────────────────────────────────

    def _gerekce_olustur(
        self,
        raf: Raf,
        urun: Urun,
        skor: float,
        mevcut_paletler: Optional[List[Palet]] = None,
    ) -> str:
        if mevcut_paletler is None:
            mevcut_paletler = self._palet_repo.getir_hepsi(
                raf_id=raf.id, sadece_aktif=True, limit=200
            )
        palet_sayisi = len(mevcut_paletler)
        ayni_urun_sayisi = sum(
            1 for p in mevcut_paletler if p.lot and p.lot.urun_id == urun.id
        )
        farkli_urun_idleri = {
            p.lot.urun_id for p in mevcut_paletler
            if p.lot and p.lot.urun_id and p.lot.urun_id != urun.id
        }
        oran = (palet_sayisi / raf.kapasite) if raf.kapasite > 0 else 1.0
        doluluk_yuzde = round(min(oran, 1.0) * 100)

        parcalar: List[str] = []
        if ayni_urun_sayisi:
            parcalar.append(f"Aynı üründen {ayni_urun_sayisi} palet mevcut")
        if len(farkli_urun_idleri) >= 2:
            parcalar.append("Karışık raf (farklı SKU'lar)")
        elif len(farkli_urun_idleri) == 1 and ayni_urun_sayisi == 0:
            parcalar.append("Farklı SKU mevcut")
        parcalar.append(f"%{doluluk_yuzde} dolu ({palet_sayisi}/{raf.kapasite} slot)")
        parcalar.append(f"Skor: {skor:.0f}/100")
        return ", ".join(parcalar)
