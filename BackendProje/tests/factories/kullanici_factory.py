import factory
from models import Kullanici
from tests.factories.base_factory import BaseFactory
from tests.conftest import get_test_password_hash


class KullaniciFactory(BaseFactory):
    class Meta:
        model = Kullanici

    kullanici_adi = factory.Sequence(lambda n: f"kullanici_{n}")
    sifre_hash = factory.LazyFunction(get_test_password_hash)
    ad_soyad = factory.Sequence(lambda n: f"Test Kullanici {n}")
    rol = "depocu"
    depo_erisimi_yok = False
