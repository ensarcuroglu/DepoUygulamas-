import factory

from models import Zon
from tests.factories.base_factory import BaseFactory
from tests.factories.depo_factory import DepoFactory


class ZonFactory(BaseFactory):
    class Meta:
        model = Zon

    depo = factory.SubFactory(DepoFactory)
    isim = factory.Sequence(lambda n: f"Test Zon {n}")
    tip = "Genel"
    kod = factory.Sequence(lambda n: f"Z{n:03d}")
    aciklama = "Test zon aciklamasi"
    sira = 0
    aktif = True

