"""Palet sorgulama servisi — read-model assembler.

Palet bilgisini DB veya veri kaynagindan (irsaliye/ERP) getirir
ve PaletBilgiDTO olarak doner. Domain service'den ayrı tutulur
cunku sadece okuma/zenginlestirme isi yapar, domain kurali icermez.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.application.dto.palet_bilgi_dto import PaletBilgiDTO
from app.core.entities.palet import Palet

if TYPE_CHECKING:
    from app.core.services.palet_veri_kaynagi_service import IPaletVeriKaynagiService
    from app.core.repositories.palet_repository import IPaletRepository
    from app.core.repositories.lot_repository import ILotRepository
    from app.core.repositories.urun_repository import IUrunRepository
    from app.core.repositories.depo_repository import IDepoRepository
    from app.core.repositories.raf_repository import IRafRepository


class PaletSorgulamaService:
    """Palet bilgisini sorgular ve PaletBilgiDTO olarak doner."""

    def __init__(
        self,
        veri_kaynagi: IPaletVeriKaynagiService,
        palet_repo: IPaletRepository,
        lot_repo: ILotRepository,
        urun_repo: IUrunRepository,
        depo_repo: IDepoRepository,
        raf_repo: IRafRepository,
    ):
        self._veri_kaynagi = veri_kaynagi
        self._palet_repo = palet_repo
        self._lot_repo = lot_repo
        self._urun_repo = urun_repo
        self._depo_repo = depo_repo
        self._raf_repo = raf_repo

    def sorgula(self, palet_no: str) -> PaletBilgiDTO:
        """Palet bilgisini getirir. Oncelik: DB paleti > veri kaynagi."""
        palet = self._palet_repo.getir_palet_no_ile(palet_no)
        if palet:
            return self._db_palet_to_dto(palet)
        return self._veri_kaynagi.palet_bilgisi_getir(palet_no)

    def _db_palet_to_dto(self, palet: Palet) -> PaletBilgiDTO:
        """DB'deki Palet entity'sinden PaletBilgiDTO olusturur."""
        lot = self._lot_repo.getir_id_ile(palet.lot_id) if palet.lot_id else None

        urun_id = lot.urun_id if lot else 0
        urun = self._urun_repo.getir_id_ile(urun_id) if urun_id else None

        depo_id = 0
        depo_adi = ""
        raf_bilgi = None
        if palet.raf_id:
            raf = self._raf_repo.getir_id_ile(palet.raf_id)
            if raf:
                depo_id = raf.depo_id or 0
                depo = self._depo_repo.getir_id_ile(depo_id) if depo_id else None
                depo_adi = depo.isim if depo else ""
                raf_bilgi = f"{depo_adi} / {raf.kod}" if depo_adi else raf.kod

        return PaletBilgiDTO(
            palet_no=palet.palet_no,
            urun_id=urun_id,
            urun_adi=urun.isim if urun else "Bilinmeyen Urun",
            urun_barkod=urun.barkod if urun else None,
            lot_no=lot.lot_no if lot else None,
            lot_id=lot.id if lot else None,
            miktar=palet.koli_adedi,
            raf_id=palet.raf_id,
            raf_bilgi=raf_bilgi,
            depo_id=depo_id,
            depo_adi=depo_adi,
            durum="aktif" if palet.aktif else "pasif",
            kaynak="sistem",
            son_kullanma_tarihi=lot.son_kullanma_tarihi if lot else None,
            giris_yapildi_mi=True,
        )
