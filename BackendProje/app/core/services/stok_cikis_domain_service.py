"""
Stok Çıkış Domain Service — FIFO mantığıyla sipariş kalemlerinden stok düşer.

Bu servis YuklemeOnaylaUseCase tarafından kullanılır. Her palet dokunuşu için
ayrı StokHareketi kaydı yazılır; bu sayede lot_id, palet_id ve raf_id hareket
üzerinde izlenebilir kalır. irsaliye_no başlangıçta None'dur; irsaliye
KESILDI/GONDERILDI durumuna geçtiğinde arka plandan doldurulur.
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
    """Sipariş kalemlerinden FIFO mantığıyla palet-bazlı stok çıkışı yapar."""

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
        kalemler: List["SiparisKalemi"],
        siparis_no: str,
        kullanici_id: int,
        tir_plaka: str | None = None,
        depo_kapi: str | None = None,
        irsaliye_no: str | None = None,
        aciklama_prefix: str = "Stok çıkışı",
        modul: str = "Stok İşlemleri",
    ) -> None:
        """Sipariş kalemleri için FIFO palet-bazlı stok çıkışı yapar.

        Her kalem için FIFO paletler kilitlenir; her palet tüketimi için ayrı
        StokHareketi kaydı üretilir (lot_id, palet_id, raf_id dolu). Stok
        yetersizliğinde hata loglanır ve üst akış transaction'ı geri alabilsin
        diye exception yeniden fırlatılır.
        """
        for kalem in kalemler:
            try:
                tuketimler = self._fifo_palet_tuket(kalem.urun_id, kalem.miktar)
                for palet_id, lot_id, raf_id, dusurulen in tuketimler:
                    hareket = StokHareketi(
                        urun_id=kalem.urun_id,
                        lot_id=lot_id,
                        palet_id=palet_id,
                        raf_id=raf_id,
                        hareket_tipi=HareketTipi.CIKIS,
                        miktar=dusurulen,
                        siparis_no=siparis_no,
                        irsaliye_no=irsaliye_no,
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
                raise

    def fifo_palet_azalt(self, urun_id: int, miktar: int) -> None:
        """Geriye dönük uyumluluk: FIFO düşümünü tetikler, hareket yazmaz."""
        self._fifo_palet_tuket(urun_id, miktar)

    def _fifo_palet_tuket(
        self, urun_id: int, miktar: int
    ) -> list[tuple[int, int, int, int]]:
        """FIFO sırasıyla paletlerden stok düşer.

        Returns:
            (palet_id, lot_id, raf_id, dusurulen_miktar) tuple listesi.
        """
        fifo_paletler = self._palet_repo.getir_fifo_sirayla_kilitli(urun_id)
        kalan = miktar
        tuketimler: list[tuple[int, int, int, int]] = []

        for palet in fifo_paletler:
            if kalan <= 0:
                break
            dusurulen = palet.stok_dus(kalan)
            if dusurulen <= 0:
                continue
            kalan -= dusurulen
            self._palet_repo.guncelle(palet, auto_commit=False)
            tuketimler.append((palet.id, palet.lot_id, palet.raf_id, dusurulen))

        if kalan > 0:
            raise StokVeriUyumsuzluguError(f"Ürün ID: {urun_id}")

        return tuketimler
