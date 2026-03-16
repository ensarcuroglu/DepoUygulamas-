import factory
from models import Kategori
from tests.factories.base_factory import BaseFactory


class KategoriFactory(BaseFactory):
    class Meta:
        model = Kategori

    isim = factory.Sequence(lambda n: f"Test Kategori {n}")
    aciklama = "Test kategori açıklaması"
    aktif = True
