"""Kapasite Doğrulama Servisi — rafın hibrit kapasitesini (slot + ağırlık) doğrular."""

from __future__ import annotations
from typing import List

from app.core.entities.raf import Raf, KapasiteSonuc
from app.core.repositories.palet_repository import IPaletRepository
from app.core.repositories.raf_repository import IRafRepository


class KapasiteDogrulamaServisi:
    """
    Rafın hibrit kapasitesini (slot sayısı + ağırlık) doğrular.

    DB'den mevcut palet durumunu çeker ve domain entity'nin
    kapasite_yeterli_mi() iş kuralını çağırır.
    """

    def __init__(self, palet_repo: IPaletRepository, raf_repo: IRafRepository):
        self._palet_repo = palet_repo
        self._raf_repo = raf_repo
        self._palet_sayfa_boyutu = 500

    def _raf_palet_ozeti_getir(self, raf_id: int) -> tuple[int, float]:
        """Raftaki tum aktif paletleri sayfali okuyup adet ve agirlik toplamini doner."""
        toplam_adet = 0
        toplam_agirlik = 0.0
        skip = 0

        while True:
            paletler = self._palet_repo.getir_hepsi(
                skip=skip,
                limit=self._palet_sayfa_boyutu,
                raf_id=raf_id,
                sadece_aktif=True,
            )
            if not paletler:
                break

            toplam_adet += len(paletler)
            toplam_agirlik += sum(p.palet_kg or 0.0 for p in paletler)

            if len(paletler) < self._palet_sayfa_boyutu:
                break
            skip += self._palet_sayfa_boyutu

        return toplam_adet, toplam_agirlik

    def dogrula(self, raf: Raf, yeni_palet_kg: float = 0.0) -> KapasiteSonuc:
        """Rafın yeni paleti kabul edip edemeyeceğini kontrol eder."""
        mevcut_palet_sayisi, mevcut_agirlik = self._raf_palet_ozeti_getir(raf.id)
        return raf.kapasite_yeterli_mi(mevcut_palet_sayisi, mevcut_agirlik, yeni_palet_kg)

    def mevcut_palet_sayisi(self, raf_id: int) -> int:
        """Raftaki aktif palet sayısını döner."""
        mevcut_adet, _ = self._raf_palet_ozeti_getir(raf_id)
        return mevcut_adet

    def doluluk_orani(self, raf: Raf) -> float:
        """0.0–1.0 arası doluluk oranı döner (slot bazlı)."""
        if raf.kapasite <= 0:
            return 1.0
        mevcut, _ = self._raf_palet_ozeti_getir(raf.id)
        return min(mevcut / raf.kapasite, 1.0)

    def alternatif_raflar_getir(
        self, zon_id: int, palet_kg: float = 0.0, limit: int = 5
    ) -> List[Raf]:
        """Kapasitesi yeterli alternatif rafları, doluluk oranı yüksekten düşüğe sıralar."""
        adaylar = self._raf_repo.getir_hepsi(zon_id=zon_id, sadece_aktif=True, limit=500)
        uygun = []
        for raf in adaylar:
            sonuc = self.dogrula(raf, palet_kg)
            if sonuc.yeterli:
                uygun.append(raf)

        # Doluluk oranı yüksek olanı tercih et (konsolidasyon)
        uygun.sort(
            key=lambda r: self.doluluk_orani(r),
            reverse=True,
        )
        return uygun[:limit]
