import factory
from datetime import date
from models import Irsaliye
from tests.factories.base_factory import BaseFactory
from tests.factories.siparis_factory import SiparisFactory


class IrsaliyeFactory(BaseFactory):
    class Meta:
        model = Irsaliye

    siparis = factory.SubFactory(SiparisFactory)
    irsaliye_no = factory.Sequence(lambda n: f"IRS-2026-{n + 1:04d}")
    irsaliye_tarihi = factory.LazyFunction(date.today)
    belge_turu = "SevkIrsaliyesi"
    tir_plaka = factory.Sequence(lambda n: f"34 XYZ {n:03d}")
    sofor_adi = "Test Sofor"
    durum = "Taslak"
