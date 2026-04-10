"""
Stok Hareketi Use Case'leri.

En kritik iş mantığı burada:
  - FIFO stok çıkışı: paleti en eski SKT'dan itibaren düşür
  - Hızlı giriş: otomatik lot + palet oluştur
  - Atomik transaction yönetimi: tüm işlemler tek commit ile kaydedilir
  - Concurrency kontrolü: SELECT FOR UPDATE ile race condition engellenir
"""

from __future__ import annotations
from typing import List, Optional
import uuid

from sqlalchemy.orm import Session

from app.core.repositories.urun_repository import IUrunRepository
from app.core.repositories.lot_repository import ILotRepository
from app.core.repositories.palet_repository import IPaletRepository
from app.core.repositories.stok_hareketi_repository import IStokHareketiRepository
from app.core.repositories.sistem_log_repository import ISistemLogRepository
from app.core.entities.stok_hareketi import StokHareketi, HareketTipi
from app.core.entities.lot import Lot
from app.core.entities.palet import Palet
from app.core.entities.sistem_log import SistemLog, IslemTipi
from app.core.exceptions import (
    KayitBulunamadiError,
    StokVeriUyumsuzluguError,
)
from app.application.dto.stok_hareketi_dto import (
    StokHareketiOlusturRequestDTO,
    StokHareketiResponseDTO,
)

_OTOMATIK_LOT_NO = "OTOMATIK-GIRIS"


# ─────────────────────────────────────────────────────────────────
# STOK HAREKETİ LİSTELE
# ─────────────────────────────────────────────────────────────────

class StokHareketiListeleUseCase:

    def __init__(self, hareket_repo: IStokHareketiRepository):
        self._hareket_repo = hareket_repo

    def execute(
        self,
        skip: int = 0,
        limit: int = 50,
        urun_id: Optional[int] = None,
        lot_id: Optional[int] = None,
        hareket_tipi: Optional[str] = None,
    ) -> List[StokHareketiResponseDTO]:
        hareketler = self._hareket_repo.getir_hepsi(
            skip=skip, limit=limit,
            urun_id=urun_id,
            lot_id=lot_id,
            hareket_tipi=hareket_tipi,
        )
        return [StokHareketiResponseDTO.from_entity(h) for h in hareketler]


# ─────────────────────────────────────────────────────────────────
# STOK HAREKETİ OLUŞTUR (FIFO dahil)
# ─────────────────────────────────────────────────────────────────

class StokHareketiOlusturUseCase:
    """
    Stok girişi veya çıkışı oluşturur.

    Çıkış (FIFO):
      1. Paletleri SELECT FOR UPDATE ile kilitle (race condition engeli).
      2. Her paletten istenen miktarı düş; palet biter → aktif=False.
      3. Stok kaydını yaz.

    Giriş (hızlı giriş):
      1. "OTOMATIK-GIRIS" lotunu bul ya da oluştur.
      2. Yeni palet oluştur (OTM-<timestamp>).
      3. Stok kaydını yaz.

    Transaction Yönetimi:
      Tüm repository çağrıları auto_commit=False ile yapılır;
      işlem sonunda tek bir db.commit() ile atomik olarak kaydedilir.
      Hata durumunda db.rollback() çağrılarak kısmi kayıtlar geri alınır.
    """

    def __init__(
        self,
        urun_repo: IUrunRepository,
        lot_repo: ILotRepository,
        palet_repo: IPaletRepository,
        hareket_repo: IStokHareketiRepository,
        log_repo: ISistemLogRepository,
        db: Session,
    ):
        self._urun_repo = urun_repo
        self._lot_repo = lot_repo
        self._palet_repo = palet_repo
        self._hareket_repo = hareket_repo
        self._log_repo = log_repo
        self._db = db

    # ── public ──────────────────────────────────────────────────

    def execute(
        self,
        dto: StokHareketiOlusturRequestDTO,
        kullanici_id: int,
    ) -> StokHareketiResponseDTO:
        hareket_entity = StokHareketi(
            urun_id=dto.urun_id,
            lot_id=dto.lot_id,
            palet_id=dto.palet_id,
            raf_id=dto.raf_id,
            hareket_tipi=dto.hareket_tipi,
            miktar=dto.miktar,
            siparis_no=dto.siparis_no,
            tir_plaka=dto.tir_plaka,
            depo_kapi=dto.depo_kapi,
            sofor_adi=dto.sofor_adi,
            tasiyici_firma=dto.tasiyici_firma,
            barkodlar=dto.barkodlar,
            aciklama=dto.aciklama,
            kullanici_id=kullanici_id,
        )
        hareket_entity.dogrula()

        urun = self._urun_repo.getir_id_ile(dto.urun_id)
        if not urun:
            raise KayitBulunamadiError("Ürün", dto.urun_id)

        try:
            if dto.hareket_tipi == HareketTipi.CIKIS:
                hareket_entity = self._cikis_isle(hareket_entity, urun)
            else:
                hareket_entity = self._giris_isle(hareket_entity)

            kaydedilen = self._hareket_repo.olustur(hareket_entity, auto_commit=False)

            islem_metni = "Giriş Yapıldı" if dto.hareket_tipi == HareketTipi.GIRIS else "Çıkış Yapıldı"
            self._log_repo.olustur(
                SistemLog.olustur(
                    kullanici_id=kullanici_id,
                    islem_tipi=IslemTipi.UPDATE,
                    modul="Stok İşlemleri",
                    detay=f"Stok {islem_metni}: {urun.isim} | miktar: {dto.miktar}",
                ),
                auto_commit=False,
            )

            self._db.commit()
            return StokHareketiResponseDTO.from_entity(kaydedilen)

        except Exception:
            self._db.rollback()
            raise

    # ── private: çıkış (FIFO) ───────────────────────────────────

    def _cikis_isle(self, hareket: StokHareketi, urun) -> StokHareketi:
        """FIFO mantığıyla palet stoklarını düşer.

        SELECT FOR UPDATE ile ilgili paletler kilitlenir;
        eşzamanlı çıkış istekleri sıralanır ve race condition engellenir.
        """
        fifo_paletler = self._palet_repo.getir_fifo_sirayla_kilitli(urun.id)
        kalan = hareket.miktar

        for palet_entity in fifo_paletler:
            if kalan <= 0:
                break
            dusurulen = palet_entity.stok_dus(kalan)
            kalan -= dusurulen
            self._palet_repo.guncelle(palet_entity, auto_commit=False)

        if kalan > 0:
            raise StokVeriUyumsuzluguError(urun.isim)

        return hareket

    # ── private: giriş (otomatik lot + palet) ────────────────────

    def _giris_isle(self, hareket: StokHareketi) -> StokHareketi:
        """Otomatik LOT bulur/oluşturur ve yeni PALET ekler."""
        lot = self._lot_repo.getir_lot_no_ile(_OTOMATIK_LOT_NO)
        if lot is None or lot.urun_id != hareket.urun_id:
            lot = self._lot_repo.olustur(
                Lot(
                    urun_id=hareket.urun_id,
                    lot_no=_OTOMATIK_LOT_NO,
                    aciklama="Hızlı Giriş ekranından oluşturulan varsayılan lot",
                ),
                auto_commit=False,
            )

        palet_no = f"OTM-{uuid.uuid4().hex[:16].upper()}"
        yeni_palet = self._palet_repo.olustur(
            Palet(
                lot_id=lot.id,
                raf_id=hareket.raf_id,
                palet_no=palet_no,
                koli_adedi=hareket.miktar,
                vardiya="Hızlı Giriş",
            ),
            auto_commit=False,
        )

        hareket.lot_id = lot.id
        hareket.palet_id = yeni_palet.id
        return hareket
