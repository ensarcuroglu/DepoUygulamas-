import factory
from models import Lot
from tests.factories.base_factory import BaseFactory
from tests.factories.urun_factory import UrunFactory


class LotFactory(BaseFactory):
    class Meta:
        model = Lot

    urun = factory.SubFactory(UrunFactory)
    lot_no = factory.Sequence(lambda n: f"LOT-{n:04d}")
    parti_no = factory.Sequence(lambda n: f"PARTI-{n:04d}")
    aktif = True
