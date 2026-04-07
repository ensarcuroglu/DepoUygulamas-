"""
Yerleştirme Algoritması — WMS endüstri standardı putaway algorithm.

Karar hiyerarşisi:
  1. Uygunluk  : Ürün depolama tipi ⊂ Zon izin verilen tipler
  2. Kapasite  : Raf slot + ağırlık kapasitesi yeterli mi
  3. Verimlilik:
     a) Konsolidasyon  (%40) — Aynı ürün olan rafa yakın
     b) Doluluk oranı  (%30) — En dolu ama hâlâ uygun rafa (boşluk konsolidasyonu)
     c) FIFO uyumu     (%20) — Aynı SKT'li ürünlerin bir arada tutulması
     d) Zon önceliği   (%10) — Tercih edilen zon sırası
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional

from app.core.entities.raf import Raf
from app.core.entities.palet import Palet
from app.core.entities.urun import Urun
from app.core.repositories.raf_repository import IRafRepository
from app.core.repositories.zon_repository import IZonRepository
from app.core.repositories.palet_repository import IPaletRepository
from app.core.services.zon_uyumluluk_servisi import ZonUyumlulukServisi
from app.core.services.kapasite_dogrulama_servisi import KapasiteDogrulamaServisi


# ── Zon tercih öncelikleri (düşük = daha önce değerlendirilir) ──
_ZON_TIPI_TERCIH = {
    "Genel": 1,
    "Soguk": 1,
    "Tehlikeli": 1,
    "MalKabul": 5,    # Staging — kalıcı depolama için tercih edilmez
    "Sevkiyat": 5,    # Dispatch — kalıcı depolama için tercih edilmez
    "Karantina": 10,  # İzole alan — algoritma buraya önermez
}
_ZON_ONCELIK_VARSAYILAN = 3


@dataclass
class YerlestirmeOnerisi:
    """Yerleştirme algoritmasının ürettiği öneri."""
    onerilen_raf: Raf
    skor: float                         # 0–100
    alternatifler: List[Raf] = field(default_factory=list)  # Top 3 alternatif
    gerekce: str = ""                   # "Aynı üründen 5 palet mevcut, %72 dolu"


class YerlestirmeAlgoritmasi:
    """
    Palet için en uygun rafı önerir.

    Domain servisi — saf hesaplama + read-only repository erişimi.
    Herhangi bir yazma işlemi yapmaz.
    """

    def __init__(
        self,
        raf_repo: IRafRepository,
        zon_repo: IZonRepository,
        palet_repo: IPaletRepository,
        zon_uyumluluk: ZonUyumlulukServisi,
        kapasite_dogrulama: KapasiteDogrulamaServisi,
    ):
        self._raf_repo = raf_repo
        self._zon_repo = zon_repo
        self._palet_repo = palet_repo
        self._zon_uyumluluk = zon_uyumluluk
        self._kapasite = kapasite_dogrulama

    # ─────────────────────────────────────────────────────────────────────────
    # Ana API
    # ─────────────────────────────────────────────────────────────────────────

    def raf_oner(self, palet: Palet, urun: Urun, depo_id: int) -> Optional[YerlestirmeOnerisi]:
        """
        Palet için en uygun rafı önerir.

        Returns:
            YerlestirmeOnerisi — ya da uygun raf yoksa None.
        """
        palet_kg = palet.palet_kg or 0.0

        # 1. Uygun zonları bul
        uygun_zonlar = self._zon_uyumluluk.uyumlu_zonlari_getir(depo_id, urun.depolama_tipi)
        # Karantina'yı algoritma önerilerinden çıkar
        uygun_zonlar = [z for z in uygun_zonlar if z.tip != "Karantina"]

        if not uygun_zonlar:
            return None

        # 2. Aday rafları topla (tüm uygun zonlardan)
        adaylar: List[Raf] = []
        for zon in uygun_zonlar:
            raflar = self._raf_repo.getir_hepsi(zon_id=zon.id, sadece_aktif=True, limit=500)
            adaylar.extend(raflar)

        if not adaylar:
            return None

        # 3. Kapasitesi yetersiz rafları elele
        uygun_raflar = [
            r for r in adaylar
            if self._kapasite.dogrula(r, palet_kg).yeterli
        ]

        if not uygun_raflar:
            return None

        # 4. Tüm adayları skorla
        skorlar = [(raf, self._skorla(raf, urun, palet)) for raf in uygun_raflar]
        skorlar.sort(key=lambda x: x[1], reverse=True)

        en_iyi_raf, en_iyi_skor = skorlar[0]
        alternatifler = [r for r, _ in skorlar[1:4]]  # Top 3 alternatif

        return YerlestirmeOnerisi(
            onerilen_raf=en_iyi_raf,
            skor=round(en_iyi_skor, 1),
            alternatifler=alternatifler,
            gerekce=self._gerekce_olustur(en_iyi_raf, urun, en_iyi_skor),
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Skorlama
    # ─────────────────────────────────────────────────────────────────────────

    def _skorla(self, raf: Raf, urun: Urun, palet: Palet) -> float:
        """Her raf için 0–100 arası bileşik skor hesaplar."""
        return (
            self._konsolidasyon_skoru(raf, urun) * 0.40
            + self._doluluk_skoru(raf) * 0.30
            + self._fifo_skoru(raf, palet) * 0.20
            + self._zon_onceligi_skoru(raf) * 0.10
        )

    def _konsolidasyon_skoru(self, raf: Raf, urun: Urun) -> float:
        """Raftaki mevcut paletler içinde aynı ürün varsa yüksek skor döner (0–100)."""
        mevcut = self._palet_repo.getir_hepsi(raf_id=raf.id, sadece_aktif=True, limit=200)
        if not mevcut:
            return 0.0
        ayni_urun = sum(
            1 for p in mevcut
            if p.lot and p.lot.urun_id == urun.id
        )
        # Her aynı ürün paleti +20 puan (max 100)
        return min(ayni_urun * 20.0, 100.0)

    def _doluluk_skoru(self, raf: Raf) -> float:
        """Doluluk oranı yüksek olanı tercih et — boşluk konsolidasyonu (0–100)."""
        return self._kapasite.doluluk_orani(raf) * 100.0

    def _fifo_skoru(self, raf: Raf, palet: Palet) -> float:
        """
        Paletin SKT'si ile raftaki en erken SKT arasındaki uyumu ölçer.
        Aynı veya yakın SKT'li ürünler bir arada olursa skor yüksek (0–100).
        """
        palet_skt = palet.lot.son_kullanma_tarihi if palet.lot else None
        if not palet_skt:
            return 50.0  # SKT bilgisi yoksa nötr skor

        mevcut = self._palet_repo.getir_hepsi(raf_id=raf.id, sadece_aktif=True, limit=200)
        skt_listesi = [
            p.lot.son_kullanma_tarihi
            for p in mevcut
            if p.lot and p.lot.son_kullanma_tarihi
        ]
        if not skt_listesi:
            return 50.0  # Boş raf — nötr

        en_erken_skt: date = min(skt_listesi)

        # Fark ne kadar az ise skor o kadar yüksek (30 gün tolerans)
        fark_gun = abs((palet_skt - en_erken_skt).days)
        return max(0.0, 100.0 - fark_gun * (100.0 / 30.0))

    def _zon_onceligi_skoru(self, raf: Raf) -> float:
        """Tercih edilen zonlar daha yüksek skor alır (0–100)."""
        zon = self._zon_repo.getir_id_ile(raf.zon_id) if raf.zon_id else None
        if not zon:
            return 50.0
        tercih = _ZON_TIPI_TERCIH.get(zon.tip, _ZON_ONCELIK_VARSAYILAN)
        # tercih 1 (en iyi) → 100, tercih 10 (en kötü) → 0
        return max(0.0, 100.0 - (tercih - 1) * (100.0 / 9.0))

    # ─────────────────────────────────────────────────────────────────────────
    # Gerekçe metni
    # ─────────────────────────────────────────────────────────────────────────

    def _gerekce_olustur(self, raf: Raf, urun: Urun, skor: float) -> str:
        mevcut = self._palet_repo.getir_hepsi(raf_id=raf.id, sadece_aktif=True, limit=200)
        palet_sayisi = len(mevcut)
        ayni_urun_sayisi = sum(
            1 for p in mevcut if p.lot and p.lot.urun_id == urun.id
        )
        doluluk = round(self._kapasite.doluluk_orani(raf) * 100)

        parcalar = []
        if ayni_urun_sayisi:
            parcalar.append(f"Aynı üründen {ayni_urun_sayisi} palet mevcut")
        parcalar.append(f"%{doluluk} dolu ({palet_sayisi}/{raf.kapasite} slot)")
        parcalar.append(f"Skor: {skor:.0f}/100")
        return ", ".join(parcalar)
