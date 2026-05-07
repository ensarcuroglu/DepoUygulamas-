"""Factory'ler — LMS (Operatör Performans).

GorevPerformansEventFactory     — append-only outbox event log
OperatorVardiyaMetrikleriFactory — vardiya KPI özeti
"""

from datetime import date, datetime

import factory

from models import GorevPerformansEvent, OperatorVardiyaMetrikleri
from tests.factories.base_factory import BaseFactory
from tests.factories.kullanici_factory import KullaniciFactory


class GorevPerformansEventFactory(BaseFactory):
    class Meta:
        model = GorevPerformansEvent

    event_tipi = "GOREV_TAMAMLANDI"
    gorev_tipi = "yerlestirme"
    gorev_id = factory.Sequence(lambda n: 1000 + n)
    kullanici = factory.SubFactory(KullaniciFactory)
    depo_id = None
    sure_saniye = 300
    iptal_nedeni = None
    payload = None
    aggregate_edildi = False
    olusturma_tarihi = factory.LazyFunction(datetime.utcnow)


class OperatorVardiyaMetrikleriFactory(BaseFactory):
    class Meta:
        model = OperatorVardiyaMetrikleri

    kullanici = factory.SubFactory(KullaniciFactory)
    depo_id = None
    vardiya_tarihi = factory.LazyFunction(date.today)
    tamamlanan_yerlestirme = 0
    tamamlanan_toplama = 0
    iptal_sayisi = 0
    toplam_aktif_saniye = 0
    ortalama_gorev_suresi_sn = 0.0
    son_guncelleme = factory.LazyFunction(datetime.utcnow)
