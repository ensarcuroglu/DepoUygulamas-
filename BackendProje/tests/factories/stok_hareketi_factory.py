import factory
from models import StokHareketi
from tests.factories.base_factory import BaseFactory
from tests.factories.urun_factory import UrunFactory
from tests.factories.kullanici_factory import KullaniciFactory


class StokHareketiFactory(BaseFactory):
    class Meta:
        model = StokHareketi

    urun = factory.SubFactory(UrunFactory)
    kullanici = factory.SubFactory(KullaniciFactory)
    hareket_tipi = "giris"
    miktar = 100
    aciklama = "Test stok hareketi"
