"""
Integration testler: IrsaliyePaletVeriKaynagiService — gercek DB ile.
"""

import pytest
from tests.factories import (
    MalKabulIrsaliyeFactory,
    MalKabulKalemiFactory,
    DepoFactory,
    UrunFactory,
    RafFactory,
    TedarikciFactory,
    LotFactory,
)

from app.infrastructure.persistence.repositories.sa_mal_kabul_irsaliye_repository import (
    SqlAlchemyMalKabulIrsaliyeRepository,
)
from app.infrastructure.persistence.repositories import (
    SqlAlchemyUrunRepository,
    SqlAlchemyDepoRepository,
    SqlAlchemyRafRepository,
    SqlAlchemyLotRepository,
)
from app.infrastructure.services.irsaliye_palet_veri_kaynagi_service import (
    IrsaliyePaletVeriKaynagiService,
)
from app.core.exceptions import KayitBulunamadiError, GecersizIslemError

pytestmark = pytest.mark.integration


@pytest.fixture
def adapter(db_session):
    """Gercek DB bagli adapter instance."""
    return IrsaliyePaletVeriKaynagiService(
        mal_kabul_repo=SqlAlchemyMalKabulIrsaliyeRepository(db_session),
        urun_repo=SqlAlchemyUrunRepository(db_session),
        depo_repo=SqlAlchemyDepoRepository(db_session),
        raf_repo=SqlAlchemyRafRepository(db_session),
        lot_repo=SqlAlchemyLotRepository(db_session),
    )


class TestPaletBilgisiGetir:

    def test_basarili_getir(self, adapter, db_session):
        depo = DepoFactory.create(isim="Ana Depo")
        tedarikci = TedarikciFactory.create()
        urun = UrunFactory.create(isim="Makarna 500g", barkod="8690000000001")
        raf = RafFactory.create(depo=depo, kod="R-01-A")

        irsaliye = MalKabulIrsaliyeFactory.create(
            depo=depo, tedarikci=tedarikci, durum="Onaylandi",
        )
        MalKabulKalemiFactory.create(
            irsaliye=irsaliye,
            palet_no="PLT-2026-00100",
            urun=urun,
            lot_no="LOT-2026-0050",
            miktar=120,
            raf=raf,
            durum="Bekliyor",
        )
        db_session.commit()

        result = adapter.palet_bilgisi_getir("PLT-2026-00100")

        assert result.palet_no == "PLT-2026-00100"
        assert result.urun_id == urun.id
        assert result.urun_adi == "Makarna 500g"
        assert result.miktar == 120
        assert result.depo_id == depo.id
        assert result.depo_adi == "Ana Depo"
        assert result.kaynak == "irsaliye"
        assert result.giris_yapildi_mi is False

    def test_bulunamadi(self, adapter):
        with pytest.raises(KayitBulunamadiError):
            adapter.palet_bilgisi_getir("PLT-YOK-99999")


class TestPaletGirisOnayla:

    def test_basarili_onay(self, adapter, db_session):
        depo = DepoFactory.create()
        tedarikci = TedarikciFactory.create()
        urun = UrunFactory.create()

        irsaliye = MalKabulIrsaliyeFactory.create(
            depo=depo, tedarikci=tedarikci, durum="Onaylandi",
        )
        MalKabulKalemiFactory.create(
            irsaliye=irsaliye,
            palet_no="PLT-2026-00200",
            urun=urun,
            miktar=50,
            durum="Bekliyor",
        )
        db_session.commit()

        adapter.palet_giris_onayla("PLT-2026-00200")
        db_session.commit()

        # Durumu dogrudan DB'den kontrol et
        updated = adapter._mal_kabul_repo.getir_kalem_palet_no_ile("PLT-2026-00200")
        assert updated.durum == "GirisYapildi"

    def test_zaten_giris_yapilmis(self, adapter, db_session):
        depo = DepoFactory.create()
        tedarikci = TedarikciFactory.create()
        urun = UrunFactory.create()

        irsaliye = MalKabulIrsaliyeFactory.create(
            depo=depo, tedarikci=tedarikci,
        )
        MalKabulKalemiFactory.create(
            irsaliye=irsaliye,
            palet_no="PLT-2026-00300",
            urun=urun,
            miktar=50,
            durum="GirisYapildi",
        )
        db_session.commit()

        with pytest.raises(GecersizIslemError, match="zaten yapilmis"):
            adapter.palet_giris_onayla("PLT-2026-00300")
