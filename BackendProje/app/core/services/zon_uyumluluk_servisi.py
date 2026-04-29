"""Zon Uyumluluk Servisi — ürün depolama tipi ile zon tipi uyumluluğunu doğrular."""

from __future__ import annotations
from typing import List

from app.core.entities.zon import Zon, ZonTipi
from app.core.repositories.zon_repository import IZonRepository


class ZonUyumlulukServisi:
    """
    Ürün depolama tipi ile zon tipi uyumluluğunu doğrular.

    Pure domain servisi — yan etkisiz metodlar ZonTipi matrisini kullanır.
    DB'ye erişen metodlar zon_repo üzerinden çalışır.
    """

    def __init__(self, zon_repo: IZonRepository):
        self._zon_repo = zon_repo
        self._zon_sayfa_boyutu = 200

    def _aktif_zonlari_getir(self, depo_id: int) -> List[Zon]:
        """Depodaki aktif zonlari sayfali sekilde tam olarak yukler."""
        tum_zonlar: List[Zon] = []
        skip = 0

        while True:
            zonlar = self._zon_repo.getir_hepsi(
                skip=skip,
                limit=self._zon_sayfa_boyutu,
                depo_id=depo_id,
                sadece_aktif=True,
            )
            if not zonlar:
                break

            tum_zonlar.extend(zonlar)

            if len(zonlar) < self._zon_sayfa_boyutu:
                break
            skip += self._zon_sayfa_boyutu

        return tum_zonlar

    def uyumlu_mu(self, depolama_tipi: str, zon_tipi: str) -> bool:
        """Ürünün bu zona yerleştirilip yerleştirilemeyeceğini kontrol eder."""
        return depolama_tipi in ZonTipi.izin_verilen_depolama_tipleri(zon_tipi)

    def uyumlu_zonlari_getir(
        self,
        depo_id: int,
        depolama_tipi: str,
        sadece_kalici_depolama: bool = False,
    ) -> List[Zon]:
        """Ürün tipiyle uyumlu, aktif tüm zonları döner.

        Args:
            sadece_kalici_depolama: True ise MalKabul/Sevkiyat/Karantina gibi
                staging/izolasyon zonları sonuçtan çıkarılır. Akıllı yerleştirme
                algoritması bu bayrağı True ile çağırır.
        """
        tum_zonlar = self._aktif_zonlari_getir(depo_id)
        sonuc = [z for z in tum_zonlar if self.uyumlu_mu(depolama_tipi, z.tip)]
        if sadece_kalici_depolama:
            sonuc = [z for z in sonuc if ZonTipi.kalici_depolama_mi(z.tip)]
        return sonuc

    def uyumsuzluk_mesaji(self, depolama_tipi: str, zon_tipi: str) -> str:
        """Frontend'e gösterilecek hata mesajını döner."""
        izinli = ZonTipi.izin_verilen_depolama_tipleri(zon_tipi)
        return (
            f"Zon Uyumsuzluğu: '{depolama_tipi}' depolama tipindeki ürün "
            f"'{zon_tipi}' zonuna yerleştirilemez. "
            f"Bu zon şunları kabul eder: {', '.join(sorted(izinli)) or 'hiçbiri'}."
        )
