import factory
from models import Urun
from tests.factories.base_factory import BaseFactory
from tests.factories.kategori_factory import KategoriFactory
from tests.factories.marka_factory import MarkaFactory


class UrunFactory(BaseFactory):
    class Meta:
        model = Urun

    isim = factory.Sequence(lambda n: f"Test Urun {n}")
    marka = factory.SubFactory(MarkaFactory)
    kategori = factory.SubFactory(KategoriFactory)
    barkod = factory.Sequence(lambda n: f"{10000000 + n:013d}")
    birim = "Adet"
    fiyat = 10.0
    min_stok = 10
    aktif = True
