import factory
from datetime import date, timedelta
from models import SevkiyatPlani
from tests.factories.base_factory import BaseFactory
from tests.factories.siparis_factory import SiparisFactory


class SevkiyatPlaniFactory(BaseFactory):
    class Meta:
        model = SevkiyatPlani

    siparis = factory.SubFactory(SiparisFactory)
    tir_plaka = factory.Sequence(lambda n: f"34 ABC {n:03d}")
    sofor_adi = "Test Sofor"
    sofor_telefon = "05551112233"
    depo_kapi = "Kapi-1"
    yukleme_tarihi = factory.LazyFunction(lambda: date.today() + timedelta(days=1))
    cikis_saati = "08:00"
    varis_saati = "16:00"
    durum = "Planlandi"
    notlar = ""
