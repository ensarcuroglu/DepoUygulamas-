import factory
from datetime import date, timedelta
from models import Siparis, SiparisKalemi
from tests.factories.base_factory import BaseFactory
from tests.factories.kullanici_factory import KullaniciFactory
from tests.factories.urun_factory import UrunFactory


class SiparisFactory(BaseFactory):
    class Meta:
        model = Siparis

    siparis_no = factory.Sequence(lambda n: f"SIP-2026-{n + 1:04d}")
    musteri_adi = factory.Sequence(lambda n: f"Test Musteri {n}")
    teslimat_adresi = "Test Adres, Istanbul"
    teslimat_tarihi = factory.LazyFunction(lambda: date.today() + timedelta(days=7))
    durum = "Bekleme"
    top_miktar = 0
    top_tutar = 0.0
    notlar = ""
    olusturan_kullanici = factory.SubFactory(KullaniciFactory, rol="admin")
    aktif = True


class SiparisKalemiFactory(BaseFactory):
    class Meta:
        model = SiparisKalemi

    siparis = factory.SubFactory(SiparisFactory)
    urun = factory.SubFactory(UrunFactory)
    miktar = 10
    birim_fiyat = 100.0
    kdv_orani = 18.0
    toplam = factory.LazyAttribute(lambda o: o.miktar * o.birim_fiyat * (1 + o.kdv_orani / 100))
