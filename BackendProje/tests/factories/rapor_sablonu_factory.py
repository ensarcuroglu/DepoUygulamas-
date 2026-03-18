import factory
from models import RaporSablonu, RaporLogu, RaporSchedule
from tests.factories.base_factory import BaseFactory
from tests.factories.kullanici_factory import KullaniciFactory


class RaporSablonuFactory(BaseFactory):
    class Meta:
        model = RaporSablonu

    ad = factory.Sequence(lambda n: f"Test Rapor Sablonu {n}")
    tur = "stok"
    aciklama = "Test rapor aciklamasi"
    config = {"columns": ["id", "isim"], "filters": {}}
    olusturan_kullanici = factory.SubFactory(KullaniciFactory, rol="admin")
    is_aktif = True


class RaporLoguFactory(BaseFactory):
    class Meta:
        model = RaporLogu

    sablon = factory.SubFactory(RaporSablonuFactory)
    kullanici = factory.SubFactory(KullaniciFactory, rol="admin")
    parametreler = {"format": "pdf"}
    durum = "Basarili"


class RaporScheduleFactory(BaseFactory):
    class Meta:
        model = RaporSchedule

    sablon = factory.SubFactory(RaporSablonuFactory)
    sablon_adi = factory.LazyAttribute(lambda o: o.sablon.ad)
    periyod = "gunluk"
    saat = "09:00"
    alici_emailler = ["test@example.com"]
    format = "pdf"
    is_aktif = True
