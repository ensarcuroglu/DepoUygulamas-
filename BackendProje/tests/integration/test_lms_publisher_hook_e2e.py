"""LMS Faz 4 — E2E publisher hook + aggregator zinciri.

Yerleştirme görevi `baslat` → `tamamla` use case'leri sırasıyla:
  1. `gorev_performans_eventleri` tablosuna 2 event yazar (BAŞLATILDI + TAMAMLANDI)
  2. Aggregator çalıştırılınca `operator_vardiya_metrikleri` tek satıra upsert eder

Bu test publisher → outbox → aggregator → KPI okuma zincirinin tamamını
gerçek MySQL bağlantısıyla doğrular.
"""

from __future__ import annotations

import pytest

from app.application.dto.yerlestirme_gorevi_dto import (
    YerlestirmeGoreviTamamlaRequestDTO,
)
from app.application.use_cases import (
    MetriklerAggregasyonUseCase,
    OperatorPerformansSorguUseCase,
    YerlestirmeGoreviBaslatUseCase,
    YerlestirmeGoreviTamamlaUseCase,
)
from app.core.services.operator_kpi_service import OperatorKpiService
from app.infrastructure.persistence.repositories import (
    SqlAlchemyGorevPerformansEventRepository,
    SqlAlchemyMalKabulIrsaliyeRepository,
    SqlAlchemyOperatorVardiyaMetrikleriRepository,
    SqlAlchemyPaletRepository,
    SqlAlchemyRafRepository,
    SqlAlchemySistemLogRepository,
    SqlAlchemyYerlestirmeGoreviRepository,
)
from app.infrastructure.services.db_outbox_performans_event_publisher import (
    DbOutboxPerformansEventPublisher,
)
from models import GorevPerformansEvent as GorevPerformansEventORM
from models import OperatorVardiyaMetrikleri as OperatorVardiyaMetrikleriORM
from tests.factories import (
    KullaniciFactory,
    RafFactory,
    YerlestirmeGoreviFactory,
)

pytestmark = pytest.mark.integration


def _build_baslat_uc(db_session) -> YerlestirmeGoreviBaslatUseCase:
    repo = SqlAlchemyYerlestirmeGoreviRepository(db_session)
    event_repo = SqlAlchemyGorevPerformansEventRepository(db_session)
    publisher = DbOutboxPerformansEventPublisher(event_repo)
    return YerlestirmeGoreviBaslatUseCase(repo, performans_publisher=publisher)


def _build_tamamla_uc(db_session) -> YerlestirmeGoreviTamamlaUseCase:
    event_repo = SqlAlchemyGorevPerformansEventRepository(db_session)
    publisher = DbOutboxPerformansEventPublisher(event_repo)
    return YerlestirmeGoreviTamamlaUseCase(
        repo=SqlAlchemyYerlestirmeGoreviRepository(db_session),
        palet_repo=SqlAlchemyPaletRepository(db_session),
        raf_repo=SqlAlchemyRafRepository(db_session),
        log_repo=SqlAlchemySistemLogRepository(db_session),
        mal_kabul_repo=SqlAlchemyMalKabulIrsaliyeRepository(db_session),
        performans_publisher=publisher,
    )


def _build_aggregator(db_session) -> MetriklerAggregasyonUseCase:
    return MetriklerAggregasyonUseCase(
        event_repo=SqlAlchemyGorevPerformansEventRepository(db_session),
        metrik_repo=SqlAlchemyOperatorVardiyaMetrikleriRepository(db_session),
        kpi_service=OperatorKpiService(),
    )


class TestPublisherHookEventYazimi:
    def test_baslat_ve_tamamla_iki_event_yazilmali(self, db_session):
        operator = KullaniciFactory.create(rol="depocu")
        hedef_raf = RafFactory.create(kapasite=10)
        gorev = YerlestirmeGoreviFactory.create(
            durum="Atandi",
            atanan_kullanici_id=operator.id,
            onerilen_raf=hedef_raf,
        )
        db_session.commit()

        # Baslat — DEVAM_EDIYOR'a geçer + GOREV_BASLATILDI event'i
        _build_baslat_uc(db_session).execute(
            gorev_id=gorev.id, kullanici_id=operator.id
        )
        # Tamamla — TAMAMLANDI'ya geçer + GOREV_TAMAMLANDI event'i (sure_saniye dolu)
        _build_tamamla_uc(db_session).execute(
            gorev_id=gorev.id,
            dto=YerlestirmeGoreviTamamlaRequestDTO(gerceklesen_raf_id=hedef_raf.id),
            kullanici_id=operator.id,
        )

        eventler = (
            db_session.query(GorevPerformansEventORM)
            .filter_by(kullanici_id=operator.id, gorev_id=gorev.id)
            .order_by(GorevPerformansEventORM.id.asc())
            .all()
        )
        assert len(eventler) == 2

        baslat_evt, tamamla_evt = eventler
        assert baslat_evt.event_tipi == "GOREV_BASLATILDI"
        assert baslat_evt.gorev_tipi == "yerlestirme"
        assert baslat_evt.aggregate_edildi is False

        assert tamamla_evt.event_tipi == "GOREV_TAMAMLANDI"
        assert tamamla_evt.sure_saniye is not None
        assert tamamla_evt.sure_saniye >= 0


class TestE2EAggregatorZinciri:
    def test_baslat_tamamla_aggregator_kpi_satiri(self, db_session):
        """
        Tam akış: baslat → tamamla → aggregator → vardiya satırı + UPH okunur.
        """
        operator = KullaniciFactory.create(rol="depocu")
        hedef_raf = RafFactory.create(kapasite=10)
        gorev = YerlestirmeGoreviFactory.create(
            durum="Atandi",
            atanan_kullanici_id=operator.id,
            onerilen_raf=hedef_raf,
        )
        db_session.commit()

        _build_baslat_uc(db_session).execute(
            gorev_id=gorev.id, kullanici_id=operator.id
        )
        _build_tamamla_uc(db_session).execute(
            gorev_id=gorev.id,
            dto=YerlestirmeGoreviTamamlaRequestDTO(gerceklesen_raf_id=hedef_raf.id),
            kullanici_id=operator.id,
        )

        sonuc = _build_aggregator(db_session).execute()
        assert sonuc.guncellenen_vardiya == 1
        # 2 event işlenir (baslat sayaca yansımaz ama event id outbox'tan temizlenir)
        assert sonuc.islenen_event == 2

        kayit = (
            db_session.query(OperatorVardiyaMetrikleriORM)
            .filter_by(kullanici_id=operator.id)
            .one()
        )
        assert kayit.tamamlanan_yerlestirme == 1
        assert kayit.tamamlanan_toplama == 0
        assert kayit.iptal_sayisi == 0
        assert kayit.toplam_aktif_saniye >= 0

        # Sorgu use case'i KPI'yi DTO'ya dönüştürebilmeli
        sorgu = OperatorPerformansSorguUseCase(
            SqlAlchemyOperatorVardiyaMetrikleriRepository(db_session)
        )
        ozet = sorgu.ozet_getir(kullanici_id=operator.id)
        assert ozet.toplam == 1
        assert ozet.items[0].kullanici_id == operator.id
        assert ozet.items[0].tamamlanan_yerlestirme == 1
