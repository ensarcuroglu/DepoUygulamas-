import factory
from models import Depo
from tests.factories.base_factory import BaseFactory


class DepoFactory(BaseFactory):
    class Meta:
        model = Depo

    isim = factory.Sequence(lambda n: f"Test Depo {n}")
    adres = "Test Adres"
    aciklama = "Test depo açıklaması"
    aktif = True
