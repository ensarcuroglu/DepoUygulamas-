import factory
from models import Palet
from tests.factories.base_factory import BaseFactory
from tests.factories.lot_factory import LotFactory
from tests.factories.raf_factory import RafFactory


class PaletFactory(BaseFactory):
    class Meta:
        model = Palet

    lot = factory.SubFactory(LotFactory)
    raf = factory.SubFactory(RafFactory)
    palet_no = factory.Sequence(lambda n: f"PLT-{n:06d}")
    koli_adedi = 10
    palet_kg = 500.0
    aktif = True
