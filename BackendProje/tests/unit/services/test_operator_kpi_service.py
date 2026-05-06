"""Unit testler: OperatorKpiService aggregasyon mantığı + entity property'leri.

Saf domain testleri — DB bağımlılığı yok.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from app.core.entities.operator_performans import (
    GorevPerformansEvent,
    OperatorVardiyaMetrikleri,
    PerformansEventTipi,
    PerformansGorevTipi,
)
from app.core.services.operator_kpi_service import OperatorKpiService

pytestmark = pytest.mark.unit


def _event(
    eid: int,
    kullanici_id: int,
    event_tipi: str,
    gorev_tipi: str,
    olusturma: datetime,
    sure: int | None = None,
    depo_id: int | None = None,
) -> GorevPerformansEvent:
    return GorevPerformansEvent(
        id=eid,
        event_tipi=event_tipi,
        gorev_tipi=gorev_tipi,
        gorev_id=1000 + eid,
        kullanici_id=kullanici_id,
        depo_id=depo_id,
        sure_saniye=sure,
        olusturma_tarihi=olusturma,
    )


# ─── OperatorKpiService.vardiya_delta_uret ───────────────────────────────


class TestVardiyaDeltaUret:
    def test_bos_event_listesi_bos_donus(self) -> None:
        sonuc = OperatorKpiService().vardiya_delta_uret([])
        assert sonuc == []

    def test_tek_kullanici_tek_gun_aggregate(self) -> None:
        gun = datetime(2026, 5, 6, 10, 0, 0)
        eventler = [
            _event(1, 7, PerformansEventTipi.GOREV_BASLATILDI,
                   PerformansGorevTipi.YERLESTIRME, gun),
            _event(2, 7, PerformansEventTipi.GOREV_TAMAMLANDI,
                   PerformansGorevTipi.YERLESTIRME, gun + timedelta(minutes=5),
                   sure=300, depo_id=2),
            _event(3, 7, PerformansEventTipi.GOREV_TAMAMLANDI,
                   PerformansGorevTipi.TOPLAMA, gun + timedelta(minutes=15),
                   sure=200, depo_id=2),
            _event(4, 7, PerformansEventTipi.GOREV_IPTAL,
                   PerformansGorevTipi.YERLESTIRME, gun + timedelta(minutes=20),
                   sure=60, depo_id=2),
        ]
        sonuc = OperatorKpiService().vardiya_delta_uret(eventler)

        assert len(sonuc) == 1
        anahtar, delta = sonuc[0]
        assert anahtar.kullanici_id == 7
        assert anahtar.vardiya_tarihi == gun.date()
        assert delta.yerlestirme_delta == 1
        assert delta.toplama_delta == 1
        assert delta.iptal_delta == 1
        assert delta.sure_saniye_delta == 560  # 300 + 200 + 60
        assert delta.depo_id == 2
        # GOREV_BASLATILDI dahil tüm event id'ler işlenmiş sayılır
        assert sorted(delta.isleneN_event_idleri) == [1, 2, 3, 4]

    def test_birden_fazla_kullanici_ayri_kovalar(self) -> None:
        gun = datetime(2026, 5, 6, 10, 0, 0)
        eventler = [
            _event(1, 7, PerformansEventTipi.GOREV_TAMAMLANDI,
                   PerformansGorevTipi.YERLESTIRME, gun, sure=300),
            _event(2, 8, PerformansEventTipi.GOREV_TAMAMLANDI,
                   PerformansGorevTipi.TOPLAMA, gun, sure=400),
        ]
        sonuc = OperatorKpiService().vardiya_delta_uret(eventler)
        assert len(sonuc) == 2
        anahtarlar = [s[0] for s in sonuc]
        # Sıralama: önce vardiya_tarihi (aynı), sonra kullanici_id ASC
        assert [a.kullanici_id for a in anahtarlar] == [7, 8]

    def test_farkli_gunler_farkli_kovalar(self) -> None:
        eventler = [
            _event(1, 7, PerformansEventTipi.GOREV_TAMAMLANDI,
                   PerformansGorevTipi.YERLESTIRME,
                   datetime(2026, 5, 5, 10, 0), sure=100),
            _event(2, 7, PerformansEventTipi.GOREV_TAMAMLANDI,
                   PerformansGorevTipi.YERLESTIRME,
                   datetime(2026, 5, 6, 10, 0), sure=200),
        ]
        sonuc = OperatorKpiService().vardiya_delta_uret(eventler)
        assert len(sonuc) == 2
        # Tarih sırası ASC
        assert sonuc[0][0].vardiya_tarihi.day == 5
        assert sonuc[1][0].vardiya_tarihi.day == 6

    def test_id_yok_olan_eventler_atlaniyor(self) -> None:
        # id=None — DB'ye yazılmamış event, aggregator atlamalı
        e = GorevPerformansEvent(
            id=None,
            event_tipi=PerformansEventTipi.GOREV_TAMAMLANDI,
            gorev_tipi=PerformansGorevTipi.YERLESTIRME,
            gorev_id=1,
            kullanici_id=7,
            sure_saniye=300,
            olusturma_tarihi=datetime(2026, 5, 6, 10, 0),
        )
        assert OperatorKpiService().vardiya_delta_uret([e]) == []

    def test_sahipsiz_event_atlaniyor(self) -> None:
        # kullanici_id=0 — sistem iptali; KPI'ya yansımaz
        e = _event(1, 0, PerformansEventTipi.GOREV_IPTAL,
                   PerformansGorevTipi.YERLESTIRME,
                   datetime(2026, 5, 6, 10, 0))
        assert OperatorKpiService().vardiya_delta_uret([e]) == []

    def test_baslama_eventi_sayaca_yansimaz(self) -> None:
        gun = datetime(2026, 5, 6, 10, 0, 0)
        e = _event(1, 7, PerformansEventTipi.GOREV_BASLATILDI,
                   PerformansGorevTipi.YERLESTIRME, gun)
        sonuc = OperatorKpiService().vardiya_delta_uret([e])
        assert len(sonuc) == 1
        _, delta = sonuc[0]
        assert delta.yerlestirme_delta == 0
        assert delta.toplama_delta == 0
        assert delta.iptal_delta == 0
        # Ama event id işlenmiş sayılır → outbox'tan temizlenir
        assert delta.isleneN_event_idleri == [1]


# ─── OperatorVardiyaMetrikleri property'leri ─────────────────────────────


class TestVardiyaMetrikleriProperties:
    def test_uph_temel_hesaplama(self) -> None:
        m = OperatorVardiyaMetrikleri(
            kullanici_id=7,
            tamamlanan_yerlestirme=10,
            tamamlanan_toplama=5,
            toplam_aktif_saniye=3600,  # 1 saat
        )
        assert m.toplam_gorev == 15
        assert m.uph == 15.0

    def test_uph_yarim_saatte_iki_kati(self) -> None:
        m = OperatorVardiyaMetrikleri(
            kullanici_id=7,
            tamamlanan_yerlestirme=10,
            toplam_aktif_saniye=1800,  # 30 dk
        )
        assert m.uph == 20.0

    def test_uph_aktif_sure_sifir_ise_sifir(self) -> None:
        m = OperatorVardiyaMetrikleri(
            kullanici_id=7,
            tamamlanan_yerlestirme=10,
            toplam_aktif_saniye=0,
        )
        assert m.uph == 0.0

    def test_hata_orani_temel(self) -> None:
        m = OperatorVardiyaMetrikleri(
            kullanici_id=7,
            tamamlanan_yerlestirme=8,
            tamamlanan_toplama=2,
            iptal_sayisi=2,
        )
        # 2 / (10 + 2) = 0.1667
        assert m.hata_orani == pytest.approx(0.1667, abs=1e-3)

    def test_hata_orani_veri_yoksa_sifir(self) -> None:
        m = OperatorVardiyaMetrikleri(kullanici_id=7)
        assert m.hata_orani == 0.0

    def test_hata_orani_sadece_iptal_varsa_bir(self) -> None:
        m = OperatorVardiyaMetrikleri(kullanici_id=7, iptal_sayisi=3)
        assert m.hata_orani == 1.0
