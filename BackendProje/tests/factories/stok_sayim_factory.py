import factory
from models import StokSayim, StokSayimKalemi
from tests.factories.base_factory import BaseFactory
from tests.factories.kullanici_factory import KullaniciFactory
from tests.factories.urun_factory import UrunFactory


class StokSayimFactory(BaseFactory):
    class Meta:
        model = StokSayim

    sayim_no = factory.Sequence(lambda n: f"SAY-202603-18-{n:04d}")
    aciklama = "Test stok sayimi"
    kontrol_eden = factory.SubFactory(KullaniciFactory, rol="admin")
    referans_stok_json = {}
    durum = "devam_ediyor"
    aktif = True


class StokSayimKalemiFactory(BaseFactory):
    class Meta:
        model = StokSayimKalemi

    sayim = factory.SubFactory(StokSayimFactory)
    urun = factory.SubFactory(UrunFactory)
    sayilan_miktar = 50
    notlar = ""
    user = factory.SubFactory(KullaniciFactory, rol="depocu")
