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
from app.core.entities.mal_kabul_irsaliye import MalKabulDurum, KalemDurum
from app.core.exceptions import KayitBulunamadiError, GecersizIslemError

pytestmark = pytest.mark.integration


@pytest.fixture
def adapter(db_session):
    return IrsaliyePaletVeriKaynagiService(
        mal_kabul_repo=SqlAlchemyMalKabulIrsaliyeRepository(db_session),
        urun_repo=SqlAlchemyUrunRepository(db_session),
        depo_repo=SqlAlchemyDepoRepository(db_session),
        raf_repo=SqlAlchemyRafRepository(db_session),
        lot_repo=SqlAlchemyLotRepository(db_session),
    )


def _make_test_kalem(db_session, palet_no, durum=KalemDurum.BEKLIYOR, **overrides):
    """Irsaliye + kalem olusturur."""
    depo = overrides.pop("depo", None) or DepoFactory.create(isim="Test Depo")
    tedarikci = overrides.pop("tedarikci", None) or TedarikciFactory.create()
    urun = overrides.pop("urun", None) or UrunFactory.create(isim="Test Urun", barkod="8690000000001")

    irsaliye = MalKabulIrsaliyeFactory.create(
        depo=depo, tedarikci=tedarikci, durum=MalKabulDurum.ONAYLANDI,
    )
    kalem = MalKabulKalemiFactory.create(
        irsaliye=irsaliye,
        palet_no=palet_no,
        urun=urun,
        lot_no="LOT-2026-0050",
        miktar=overrides.get("miktar", 100),
        durum=durum,
    )
    db_session.commit()
    return depo, urun, irsaliye, kalem


class TestPaletBilgisiGetir:

    def test_basarili_getir(self, adapter, db_session):
        depo = DepoFactory.create(isim="Ana Depo")
        urun = UrunFactory.create(isim="Makarna 500g", barkod="8690000000001")
        raf = RafFactory.create(depo=depo, kod="R-01-A")

        _make_test_kalem(
            db_session, "PLT-2026-00100",
            depo=depo, urun=urun, miktar=120,
        )

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
        _make_test_kalem(db_session, "PLT-2026-00200")

        adapter.palet_giris_onayla("PLT-2026-00200")
        db_session.commit()

        # Public interface uzerinden dogrula
        result = adapter.palet_bilgisi_getir("PLT-2026-00200")
        assert result.giris_yapildi_mi is True

    def test_zaten_giris_yapilmis(self, adapter, db_session):
        _make_test_kalem(db_session, "PLT-2026-00300", durum=KalemDurum.GIRIS_YAPILDI)

        with pytest.raises(GecersizIslemError, match="zaten yapilmis"):
            adapter.palet_giris_onayla("PLT-2026-00300")
