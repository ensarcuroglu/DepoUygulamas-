import factory
from datetime import date
from models import MalKabulIrsaliye, MalKabulKalemi
from tests.factories.base_factory import BaseFactory
from tests.factories.tedarikci_factory import TedarikciFactory
from tests.factories.depo_factory import DepoFactory
from tests.factories.urun_factory import UrunFactory
from app.core.entities.mal_kabul_irsaliye import MalKabulDurum, KalemDurum


class MalKabulIrsaliyeFactory(BaseFactory):
    class Meta:
        model = MalKabulIrsaliye

    irsaliye_no = factory.Sequence(lambda n: f"MKI-2026-{n:05d}")
    tedarikci = factory.SubFactory(TedarikciFactory)
    depo = factory.SubFactory(DepoFactory)
    durum = MalKabulDurum.ONAYLANDI
    tarih = factory.LazyFunction(date.today)


class MalKabulKalemiFactory(BaseFactory):
    class Meta:
        model = MalKabulKalemi

    irsaliye = factory.SubFactory(MalKabulIrsaliyeFactory)
    palet_no = factory.Sequence(lambda n: f"PLT-2026-{n:05d}")
    urun = factory.SubFactory(UrunFactory)
    lot_no = factory.Sequence(lambda n: f"LOT-2026-{n:04d}")
    miktar = 100
    durum = KalemDurum.BEKLIYOR
