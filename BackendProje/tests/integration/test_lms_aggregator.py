"""LMS Faz 4 — Aggregator integration testleri.

Gerçek MySQL test DB'siyle:
  (a) outbox event → vardiya KPI upsert
  (b) idempotent: işlenmiş event'ler 2. çağrıda atlanır
  (c) iptal event sayacı +1
  (d) farklı kullanıcı/gün için ayrı satır

APScheduler içinde çalışan `MetriklerAggregasyonUseCase`'in tam
zincirini doğrular: SqlAlchemyGorevPerformansEventRepository
→ OperatorKpiService → SqlAlchemyOperatorVardiyaMetrikleriRepository.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.application.use_cases import MetriklerAggregasyonUseCase
from app.core.entities.operator_performans import (
    PerformansEventTipi,
    PerformansGorevTipi,
)
from app.core.services.operator_kpi_service import OperatorKpiService
from app.infrastructure.persistence.repositories import (
    SqlAlchemyGorevPerformansEventRepository,
    SqlAlchemyOperatorVardiyaMetrikleriRepository,
)
from models import GorevPerformansEvent as GorevPerformansEventORM
from models import OperatorVardiyaMetrikleri as OperatorVardiyaMetrikleriORM
from tests.factories import (
    DepoFactory,
    GorevPerformansEventFactory,
    KullaniciFactory,
)

pytestmark = pytest.mark.integration


def _aggregator(db_session) -> MetriklerAggregasyonUseCase:
    return MetriklerAggregasyonUseCase(
        event_repo=SqlAlchemyGorevPerformansEventRepository(db_session),
        metrik_repo=SqlAlchemyOperatorVardiyaMetrikleriRepository(db_session),
        kpi_service=OperatorKpiService(),
    )


class TestAggregatorTemelAkis:
    def test_eventler_vardiya_metrigine_donusur(self, db_session):
        """Tek operatör/tek gün — 2 tamamlanma + 1 iptal → upsert."""
        op = KullanciKurulumu(db_session)
        gun = datetime(2026, 5, 6, 9, 0, 0)

        GorevPerformansEventFactory.create(
            kullanici=op.kullanici,
            depo_id=op.depo_id,
            event_tipi=PerformansEventTipi.GOREV_TAMAMLANDI,
            gorev_tipi=PerformansGorevTipi.YERLESTIRME,
            sure_saniye=300,
            olusturma_tarihi=gun,
        )
        GorevPerformansEventFactory.create(
            kullanici=op.kullanici,
            depo_id=op.depo_id,
            event_tipi=PerformansEventTipi.GOREV_TAMAMLANDI,
            gorev_tipi=PerformansGorevTipi.TOPLAMA,
            sure_saniye=200,
            olusturma_tarihi=gun + timedelta(minutes=10),
        )
        GorevPerformansEventFactory.create(
            kullanici=op.kullanici,
            depo_id=op.depo_id,
            event_tipi=PerformansEventTipi.GOREV_IPTAL,
            gorev_tipi=PerformansGorevTipi.YERLESTIRME,
            iptal_nedeni="adres bulunamadı",
            sure_saniye=60,
            olusturma_tarihi=gun + timedelta(minutes=20),
        )

        sonuc = _aggregator(db_session).execute()

        assert sonuc.islenen_event == 3
        assert sonuc.guncellenen_vardiya == 1

        kayit = (
            db_session.query(OperatorVardiyaMetrikleriORM)
            .filter_by(kullanici_id=op.kullanici.id)
            .one()
        )
        assert kayit.vardiya_tarihi == gun.date()
        assert kayit.depo_id == op.depo_id
        assert kayit.tamamlanan_yerlestirme == 1
        assert kayit.tamamlanan_toplama == 1
        assert kayit.iptal_sayisi == 1
        assert kayit.toplam_aktif_saniye == 560  # 300 + 200 + 60

        # Tüm event'ler işaretlenmiş olmalı
        islenmemis = (
            db_session.query(GorevPerformansEventORM)
            .filter_by(aggregate_edildi=False)
            .count()
        )
        assert islenmemis == 0


class TestAggregatorIdempotent:
    def test_ikinci_calistirma_islenmis_eventleri_atlar(self, db_session):
        """Aynı event seti 2 kez aggregate edilirse sayaç bir kez artar."""
        op = KullanciKurulumu(db_session)
        gun = datetime(2026, 5, 6, 10, 0, 0)
        GorevPerformansEventFactory.create(
            kullanici=op.kullanici,
            depo_id=op.depo_id,
            event_tipi=PerformansEventTipi.GOREV_TAMAMLANDI,
            gorev_tipi=PerformansGorevTipi.YERLESTIRME,
            sure_saniye=400,
            olusturma_tarihi=gun,
        )

        agg = _aggregator(db_session)
        ilk = agg.execute()
        ikinci = agg.execute()

        assert ilk.islenen_event == 1
        assert ikinci.islenen_event == 0
        assert ikinci.guncellenen_vardiya == 0

        kayit = (
            db_session.query(OperatorVardiyaMetrikleriORM)
            .filter_by(kullanici_id=op.kullanici.id)
            .one()
        )
        assert kayit.tamamlanan_yerlestirme == 1
        assert kayit.toplam_aktif_saniye == 400

    def test_yeni_eventler_eklenince_sayac_kademeli_artar(self, db_session):
        """1. çağrı: 1 görev. Yeni event eklenip 2. çağrı: sayaç toplamı 2 olur."""
        op = KullanciKurulumu(db_session)
        gun = datetime(2026, 5, 7, 9, 0, 0)

        GorevPerformansEventFactory.create(
            kullanici=op.kullanici,
            depo_id=op.depo_id,
            event_tipi=PerformansEventTipi.GOREV_TAMAMLANDI,
            gorev_tipi=PerformansGorevTipi.YERLESTIRME,
            sure_saniye=300,
            olusturma_tarihi=gun,
        )
        agg = _aggregator(db_session)
        agg.execute()

        # Yeni event ekle, tekrar çalıştır
        GorevPerformansEventFactory.create(
            kullanici=op.kullanici,
            depo_id=op.depo_id,
            event_tipi=PerformansEventTipi.GOREV_TAMAMLANDI,
            gorev_tipi=PerformansGorevTipi.TOPLAMA,
            sure_saniye=400,
            olusturma_tarihi=gun + timedelta(minutes=15),
        )
        sonuc = agg.execute()
        assert sonuc.islenen_event == 1

        kayit = (
            db_session.query(OperatorVardiyaMetrikleriORM)
            .filter_by(kullanici_id=op.kullanici.id)
            .one()
        )
        assert kayit.tamamlanan_yerlestirme == 1
        assert kayit.tamamlanan_toplama == 1
        assert kayit.toplam_aktif_saniye == 700


class TestAggregatorAyirma:
    def test_farkli_kullanicilar_ayri_satira_yazilir(self, db_session):
        op1 = KullanciKurulumu(db_session)
        op2 = KullanciKurulumu(db_session)
        gun = datetime(2026, 5, 8, 9, 0, 0)

        for op in (op1, op2):
            GorevPerformansEventFactory.create(
                kullanici=op.kullanici,
                depo_id=op.depo_id,
                event_tipi=PerformansEventTipi.GOREV_TAMAMLANDI,
                gorev_tipi=PerformansGorevTipi.YERLESTIRME,
                sure_saniye=300,
                olusturma_tarihi=gun,
            )

        sonuc = _aggregator(db_session).execute()
        assert sonuc.guncellenen_vardiya == 2

        kullanici_idleri = {
            r.kullanici_id
            for r in db_session.query(OperatorVardiyaMetrikleriORM).all()
        }
        assert kullanici_idleri == {op1.kullanici.id, op2.kullanici.id}

    def test_farkli_gunler_ayri_satira_yazilir(self, db_session):
        op = KullanciKurulumu(db_session)
        for delta_gun in (0, 1):
            GorevPerformansEventFactory.create(
                kullanici=op.kullanici,
                depo_id=op.depo_id,
                event_tipi=PerformansEventTipi.GOREV_TAMAMLANDI,
                gorev_tipi=PerformansGorevTipi.YERLESTIRME,
                sure_saniye=300,
                olusturma_tarihi=datetime(2026, 5, 9, 9, 0, 0)
                + timedelta(days=delta_gun),
            )

        sonuc = _aggregator(db_session).execute()
        assert sonuc.guncellenen_vardiya == 2

        kayitlar = (
            db_session.query(OperatorVardiyaMetrikleriORM)
            .filter_by(kullanici_id=op.kullanici.id)
            .all()
        )
        assert len(kayitlar) == 2
        tarihler = sorted(k.vardiya_tarihi for k in kayitlar)
        assert tarihler[1] - tarihler[0] == timedelta(days=1)


class TestAggregatorBosCalisma:
    def test_event_yoksa_islem_yapmaz(self, db_session):
        sonuc = _aggregator(db_session).execute()
        assert sonuc.islenen_event == 0
        assert sonuc.guncellenen_vardiya == 0
        assert (
            db_session.query(OperatorVardiyaMetrikleriORM).count() == 0
        )


# ─── Yardımcı: tek satırda kullanıcı + depo kur ─────────────────────────


class KullanciKurulumu:
    def __init__(self, db_session):
        self.depo = DepoFactory.create()
        self.kullanici = KullaniciFactory.create(rol="depocu")
        db_session.commit()
        self.depo_id = self.depo.id
