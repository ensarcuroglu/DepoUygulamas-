import factory
from models import Tedarikci
from tests.factories.base_factory import BaseFactory


class TedarikciFactory(BaseFactory):
    class Meta:
        model = Tedarikci

    firma_adi = factory.Sequence(lambda n: f"Test Tedarikci {n}")
    iletisim_kisi = "Test Kisi"
    telefon = "05551234567"
    aktif = True
