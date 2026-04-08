import factory
from models import Raf
from tests.factories.base_factory import BaseFactory
from tests.factories.depo_factory import DepoFactory


class RafFactory(BaseFactory):
    class Meta:
        model = Raf

    depo = factory.SubFactory(DepoFactory)
    kod = factory.Sequence(lambda n: f"A-{n:02d}")
    bolge = "Zemin Kat"
    kapasite = 100
    aktif = True
    is_staging = False
