"""
FEFO Seçim Servisi — First Expired, First Out.

Palet listesini son kullanma tarihine göre sıralar.
Sıralama önceliği: son_kullanma_tarihi ASC (None en sona), üretim_tarihi ASC, palet.id ASC.
"""

from __future__ import annotations
from datetime import date
from typing import List, Optional

from app.core.entities.palet import Palet


class FEFOSecimServisi:

    def uygun_paletleri_sirala(self, paletler: List[Palet]) -> List[Palet]:
        """FEFO sıralamasıyla palet listesini döner.

        Sıralama kriteri:
        1. son_kullanma_tarihi ASC (None olan paletler en sona)
        2. üretim_tarihi ASC (None olan paletler en sona)
        3. palet.id ASC (tie-breaker)
        """
        def skt_anahtar(p: Palet) -> tuple:
            skt = self._lot_skti(p)
            uretim = self._lot_uretim(p)
            # None değerler için maksimum değer kullan (en sona al)
            skt_key = (1, skt) if skt is not None else (2, date.max)
            uretim_key = (1, uretim) if uretim is not None else (2, date.max)
            return (skt_key, uretim_key, p.id or 0)

        return sorted(paletler, key=skt_anahtar)

    def rezervasyon_disi_palet(
        self,
        paletler: List[Palet],
        rezerveli_palet_ids: List[int],
    ) -> List[Palet]:
        """Aktif rezervasyon olan paletleri listeden çıkarır."""
        rezerveli_set = set(rezerveli_palet_ids)
        return [p for p in paletler if p.id not in rezerveli_set]

    def uygun_ve_siralanmis(
        self,
        paletler: List[Palet],
        rezerveli_palet_ids: Optional[List[int]] = None,
    ) -> List[Palet]:
        """Rezerve olmayanları filtreler + FEFO sıralar.

        Args:
            paletler: Aktif palet listesi (urun_id bazlı filtre yapan caller sağlar).
            rezerveli_palet_ids: Hali hazırda başka siparişlere rezerve palet ID'leri.

        Returns:
            FEFO sıralı, rezerve dışı palet listesi.
        """
        if rezerveli_palet_ids:
            paletler = self.rezervasyon_disi_palet(paletler, rezerveli_palet_ids)
        return self.uygun_paletleri_sirala(paletler)

    # ── Yardımcılar ──

    @staticmethod
    def _lot_skti(palet: Palet) -> Optional[date]:
        """Palet nesnesinden SKT okur (lot nested veya lot_id üzerinden)."""
        if palet.lot and palet.lot.son_kullanma_tarihi:
            return palet.lot.son_kullanma_tarihi
        return None

    @staticmethod
    def _lot_uretim(palet: Palet) -> Optional[date]:
        if palet.lot and palet.lot.uretim_tarihi:
            return palet.lot.uretim_tarihi
        return None
