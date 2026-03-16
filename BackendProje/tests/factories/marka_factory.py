import factory
from models import Marka
from tests.factories.base_factory import BaseFactory


class MarkaFactory(BaseFactory):
    class Meta:
        model = Marka

    isim = factory.Sequence(lambda n: f"Test Marka {n}")
    aciklama = "Test marka açıklaması"
    aktif = True
