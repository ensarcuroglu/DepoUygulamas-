"""Irsaliye bazli palet veri kaynagi adapter'i.

MalKabulKalemi kayitlarindan palet bilgisi okur.
ERP entegrasyonunda bu sinif ErpPaletVeriKaynagiService ile degistirilir.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.application.dto.palet_bilgi_dto import PaletBilgiDTO
from app.core.entities.mal_kabul_irsaliye import KalemDurum, MalKabulDurum # MalKabulDurum eklendi
from app.core.exceptions import KayitBulunamadiError, GecersizIslemError
from app.core.services.palet_veri_kaynagi_service import IPaletVeriKaynagiService

if TYPE_CHECKING:
    from app.core.repositories.mal_kabul_irsaliye_repository import IMalKabulIrsaliyeRepository
    from app.core.repositories.urun_repository import IUrunRepository
    from app.core.repositories.depo_repository import IDepoRepository
    from app.core.repositories.raf_repository import IRafRepository
    from app.core.repositories.lot_repository import ILotRepository


class IrsaliyePaletVeriKaynagiService(IPaletVeriKaynagiService):
    """MalKabulKalemi'nden palet bilgisi okuyan adapter."""

    def __init__(
        self,
        mal_kabul_repo: IMalKabulIrsaliyeRepository,
        urun_repo: IUrunRepository,
        depo_repo: IDepoRepository,
        raf_repo: IRafRepository,
        lot_repo: ILotRepository,
    ):
        self._mal_kabul_repo = mal_kabul_repo
        self._urun_repo = urun_repo
        self._depo_repo = depo_repo
        self._raf_repo = raf_repo
        self._lot_repo = lot_repo

    def palet_bilgisi_getir(self, palet_no: str) -> PaletBilgiDTO:
        kalem = self._mal_kabul_repo.getir_kalem_palet_no_ile(palet_no)
        if not kalem:
            raise KayitBulunamadiError("Palet", palet_no)

        # PYRIGHT DÜZELTMESİ: Tip daraltma (Type Narrowing) ile None kontrolü
        if kalem.mal_kabul_irsaliyesi_id is None:
            raise GecersizIslemError(f"Palet ({palet_no}) kaydina ait bir irsaliye ID bulunamadi.")

        # Irsaliye'den depo bilgisini al
        irsaliye = self._mal_kabul_repo.getir_id_ile(kalem.mal_kabul_irsaliyesi_id)
        if not irsaliye:
            raise KayitBulunamadiError("Mal Kabul Irsaliyesi", kalem.mal_kabul_irsaliyesi_id)

        # Bilgi okumak için ONAYLANDI veya KAPANDI olabilir.
        # Sadece TASLAK durumunda bilgi okunmasını engelliyoruz.
        if irsaliye.durum not in [MalKabulDurum.ONAYLANDI, MalKabulDurum.KAPANDI]:
            raise GecersizIslemError(
                f"Taslak halindeki irsaliyelerden palet bilgisi okunamaz. Mevcut durum: {irsaliye.durum}"
            )

        # Urun bilgisi
        urun = self._urun_repo.getir_id_ile(kalem.urun_id)
        urun_adi = urun.isim if urun else "Bilinmeyen Urun"
        urun_barkod = urun.barkod if urun else None

        # Depo bilgisi
        depo = self._depo_repo.getir_id_ile(irsaliye.depo_id)
        depo_adi = depo.isim if depo else "Bilinmeyen Depo"

        # Raf bilgisi (opsiyonel)
        raf_bilgi = None
        if kalem.raf_id:
            raf = self._raf_repo.getir_id_ile(kalem.raf_id)
            if raf:
                raf_bilgi = f"{depo_adi} / {raf.kod}"

        # Lot bilgisi (DB'de varsa id'sini al)
        lot_id = None
        if kalem.lot_no:
            lot = self._lot_repo.getir_lot_no_ile(kalem.lot_no)
            if lot:
                lot_id = lot.id

        return PaletBilgiDTO(
            palet_no=kalem.palet_no,
            urun_id=kalem.urun_id,
            urun_adi=urun_adi,
            urun_barkod=urun_barkod,
            lot_no=kalem.lot_no,
            lot_id=lot_id,
            miktar=kalem.miktar,
            raf_id=kalem.raf_id,
            raf_bilgi=raf_bilgi,
            depo_id=irsaliye.depo_id,
            depo_adi=depo_adi,
            irsaliye_no=irsaliye.irsaliye_no,
            durum="aktif",
            kaynak="irsaliye",
            son_kullanma_tarihi=kalem.son_kullanma_tarihi,
            giris_yapildi_mi=(kalem.durum == KalemDurum.GIRIS_YAPILDI),
        )

    def palet_giris_onayla(self, palet_no: str) -> None:
        kalem = self._mal_kabul_repo.getir_kalem_palet_no_ile(palet_no)
        if not kalem:
            raise KayitBulunamadiError("Palet", palet_no)

        if kalem.durum == KalemDurum.GIRIS_YAPILDI:
            raise GecersizIslemError("Bu palet icin giris zaten yapilmis.")

        # PYRIGHT DÜZELTMESİ: Tip daraltma (Type Narrowing) ile None kontrolü
        if kalem.mal_kabul_irsaliyesi_id is None:
            raise GecersizIslemError(f"Palet ({palet_no}) kaydina ait bir irsaliye ID bulunamadi.")

        # Irsaliye entity'sini getir ve kalemini guncelle
        irsaliye = self._mal_kabul_repo.getir_id_ile(kalem.mal_kabul_irsaliyesi_id)
        if not irsaliye:
            raise KayitBulunamadiError("Mal Kabul Irsaliyesi", kalem.mal_kabul_irsaliyesi_id)

        # KONTROL 2: Stok olusurken irsaliyenin hala Onayli oldugundan emin ol (Adım 1)
        if irsaliye.durum != MalKabulDurum.ONAYLANDI:
            raise GecersizIslemError(
                f"Sadece onaylanmis irsaliyeler uzerinden palet girisi yapilabilir. Mevcut durum: {irsaliye.durum}"
            )

        # Irsaliye'deki ilgili kalemi bul ve durumunu guncelle
        for irs_kalem in irsaliye.kalemler:
            if irs_kalem.palet_no == palet_no:
                irs_kalem.giris_yapildi()
                break
        
        # KONTROL 3: Tum kalemler girildi mi? (Adım 2)
        if irsaliye.tum_kalemler_girildi_mi():
            irsaliye.kapat()

        self._mal_kabul_repo.guncelle(irsaliye, auto_commit=False)