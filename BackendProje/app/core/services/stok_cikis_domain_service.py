"""
Stok Çıkış Domain Service — FIFO mantığıyla sipariş kalemlerinden stok düşer.

Bu servis İrsaliye ve Sevkiyat Planlama modülleri tarafından ortaklaşa kullanılır.
Tek sorumluluk: sipariş kalemleri üzerinden FIFO palet stok düşüşü + StokHareketi kaydı.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, List

from app.core.entities.stok_hareketi import StokHareketi, HareketTipi
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.exceptions import StokVeriUyumsuzluguError

if TYPE_CHECKING:
    from app.core.entities.siparis import SiparisKalemi
    from app.core.repositories.palet_repository import IPaletRepository
    from app.core.repositories.stok_hareketi_repository import IStokHareketiRepository
    from app.core.repositories.sistem_log_repository import ISistemLogRepository


class StokCikisDomainService:
    """Sipariş kalemlerinden FIFO mantığıyla stok çıkışı yapar."""

    def __init__(
        self,
        palet_repo: IPaletRepository,
        hareket_repo: IStokHareketiRepository,
        log_repo: ISistemLogRepository,
    ):
        self._palet_repo = palet_repo
        self._hareket_repo = hareket_repo
        self._log_repo = log_repo

    def siparis_bazli_stok_cikisi(
        self,
        kalemler: List[SiparisKalemi],
        siparis_no: str,
        kullanici_id: int,
        tir_plaka: str | None = None,
        depo_kapi: str | None = None,
        aciklama_prefix: str = "Stok çıkışı",
        modul: str = "Stok İşlemleri",
    ) -> None:
        """Sipariş kalemleri için FIFO stok çıkışı yapar.

        Her kalem için:
        1. Paletleri FIFO sırasıyla kilitler (SELECT FOR UPDATE).
        2. İstenen miktarı düşer.
        3. StokHareketi kaydı oluşturur.

        Stok yetersizliğinde hata loglanır ve diğer kalemlere devam edilir.
        Programlama hataları (AttributeError, TypeError vb.) yutulmaz, yeniden fırlatılır.
        """
        for kalem in kalemler:
            try:
                self._fifo_palet_azalt(kalem.urun_id, kalem.miktar)
                hareket = StokHareketi(
                    urun_id=kalem.urun_id,
                    hareket_tipi=HareketTipi.CIKIS,
                    miktar=kalem.miktar,
                    siparis_no=siparis_no,
                    tir_plaka=tir_plaka,
                    depo_kapi=depo_kapi,
                    aciklama=aciklama_prefix,
                    kullanici_id=kullanici_id,
                )
                self._hareket_repo.olustur(hareket, auto_commit=False)
            except StokVeriUyumsuzluguError as e:
                self._log_repo.olustur(
                    SistemLog.olustur(
                        kullanici_id=kullanici_id,
                        islem_tipi=IslemTipi.ERROR,
                        modul=modul,
                        detay=f"Stok çıkışı hatası (Ürün ID: {kalem.urun_id}): {str(e)}",
                    ),
                    auto_commit=False,
                )

    def fifo_palet_azalt(self, urun_id: int, miktar: int) -> None:
        """FIFO sırasıyla paletlerden stok düşer. Dışarıdan da çağrılabilir."""
        self._fifo_palet_azalt(urun_id, miktar)

    def _fifo_palet_azalt(self, urun_id: int, miktar: int) -> None:
        fifo_paletler = self._palet_repo.getir_fifo_sirayla_kilitli(urun_id)
        kalan = miktar

        for palet in fifo_paletler:
            if kalan <= 0:
                break
            dusurulen = palet.stok_dus(kalan)
            kalan -= dusurulen
            self._palet_repo.guncelle(palet, auto_commit=False)

        if kalan > 0:
            raise StokVeriUyumsuzluguError(f"Ürün ID: {urun_id}")
