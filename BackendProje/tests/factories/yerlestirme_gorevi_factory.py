import factory
from models import YerlestirmeGorevi
from tests.factories.base_factory import BaseFactory
from tests.factories.palet_factory import PaletFactory
from tests.factories.raf_factory import RafFactory


class YerlestirmeGoreviFactory(BaseFactory):
    class Meta:
        model = YerlestirmeGorevi

    palet = factory.SubFactory(PaletFactory)
    onerilen_raf = factory.SubFactory(RafFactory)
    tip = "Yerlestirme"
    durum = "Bekliyor"
    oncelik = 5
    atanan_kullanici_id = None
    override_kullanici_id = None
    override_neden = None
    gerceklesen_raf_id = None
    kaynak_raf_id = None
    mal_kabul_irsaliye_id = None
    depo_id = factory.SelfAttribute("onerilen_raf.depo_id")
    baslama_tarihi = None
    tamamlanma_tarihi = None
    iptal_nedeni = None
