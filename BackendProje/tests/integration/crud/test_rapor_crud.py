"""Integration testler: Rapor CRUD + Veri Üretimi — gerçek MySQL DB ile."""

import pytest
from datetime import date, timedelta
from crud.rapor_crud import (
    get_rapor_sablonlari,
    get_rapor_sablonu,
    create_rapor_sablonu,
    update_rapor_sablonu,
    delete_rapor_sablonu,
    get_rapor_loglari,
    create_rapor_logu,
    get_rapor_schedules,
    create_rapor_schedule,
    update_rapor_schedule,
    delete_rapor_schedule,
    get_stok_raporu_verileri,
    get_kritik_stok_raporu,
    get_abc_analiz,
    get_depo_doluluk,
    get_skt_raporu,
)
from schemas import (
    RaporSablonuCreate,
    RaporSablonuUpdate,
    RaporLoguCreate,
    RaporScheduleCreate,
    RaporScheduleUpdate,
)
from models import SistemLog
from tests.factories import (
    KullaniciFactory,
    RaporSablonuFactory,
    RaporLoguFactory,
    RaporScheduleFactory,
    UrunFactory,
    LotFactory,
    PaletFactory,
    RafFactory,
    SiparisFactory,
    SiparisKalemiFactory,
)

pytestmark = pytest.mark.integration


# ========================
# RAPOR SABLONU TESTLERI
# ========================

class TestRaporSablonuCrud:

    def test_create_rapor_sablonu(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        dto = RaporSablonuCreate(ad="Stok Raporu", tur="stok", aciklama="Stok durumu")

        result = create_rapor_sablonu(db_session, dto, kullanici.id)

        assert result.id is not None
        assert result.ad == "Stok Raporu"
        assert result.tur == "stok"
        assert result.is_aktif is True

    def test_get_rapor_sablonlari(self, db_session):
        RaporSablonuFactory.create(tur="stok")
        RaporSablonuFactory.create(tur="siparis")
        RaporSablonuFactory.create(is_aktif=False)

        result = get_rapor_sablonlari(db_session)

        assert len(result) == 2

    def test_get_rapor_sablonlari_tur_filtre(self, db_session):
        RaporSablonuFactory.create(tur="stok")
        RaporSablonuFactory.create(tur="siparis")

        result = get_rapor_sablonlari(db_session, tur="stok")

        assert len(result) == 1
        assert result[0].tur == "stok"

    def test_get_rapor_sablonu_by_id(self, db_session):
        sablon = RaporSablonuFactory.create()

        result = get_rapor_sablonu(db_session, sablon.id)

        assert result is not None
        assert result.id == sablon.id

    def test_update_rapor_sablonu(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        sablon = RaporSablonuFactory.create(ad="Eski Ad")

        dto = RaporSablonuUpdate(ad="Yeni Ad")
        result = update_rapor_sablonu(db_session, sablon.id, dto, kullanici.id)

        assert result.ad == "Yeni Ad"

    def test_update_rapor_sablonu_bulunamadi(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        dto = RaporSablonuUpdate(ad="X")

        result = update_rapor_sablonu(db_session, 99999, dto, kullanici.id)

        assert result is None

    def test_delete_rapor_sablonu_soft(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        sablon = RaporSablonuFactory.create()

        result = delete_rapor_sablonu(db_session, sablon.id, kullanici.id)

        assert result is True
        deleted = get_rapor_sablonu(db_session, sablon.id)
        assert deleted.is_aktif is False

    def test_delete_rapor_sablonu_bulunamadi(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")

        result = delete_rapor_sablonu(db_session, 99999, kullanici.id)

        assert result is False


# ========================
# RAPOR LOGU TESTLERI
# ========================

class TestRaporLoguCrud:

    def test_create_rapor_logu(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        sablon = RaporSablonuFactory.create()

        dto = RaporLoguCreate(
            sablon_id=sablon.id,
            parametreler={"format": "pdf"},
            durum="Basarili",
        )

        result = create_rapor_logu(db_session, dto, kullanici.id)

        assert result.id is not None
        assert result.sablon_id == sablon.id
        assert result.tamamlanma_tarihi is not None

    def test_get_rapor_loglari(self, db_session):
        RaporLoguFactory.create()
        RaporLoguFactory.create()

        result = get_rapor_loglari(db_session)

        assert len(result) == 2

    def test_get_rapor_loglari_sablon_filtre(self, db_session):
        sablon = RaporSablonuFactory.create()
        RaporLoguFactory.create(sablon=sablon)
        RaporLoguFactory.create()  # farklı sablon

        result = get_rapor_loglari(db_session, sablon_id=sablon.id)

        assert len(result) == 1


# ========================
# RAPOR SCHEDULE TESTLERI
# ========================

class TestRaporScheduleCrud:

    def test_create_rapor_schedule(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        sablon = RaporSablonuFactory.create()

        dto = RaporScheduleCreate(
            sablon_id=sablon.id,
            sablon_adi=sablon.ad,
            periyod="gunluk",
            saat="09:00",
            format="pdf",
        )

        result = create_rapor_schedule(db_session, dto, kullanici.id)

        assert result.id is not None
        assert result.periyod == "gunluk"

    def test_get_rapor_schedules(self, db_session):
        RaporScheduleFactory.create()
        RaporScheduleFactory.create(is_aktif=False)

        result = get_rapor_schedules(db_session)

        assert len(result) == 1

    def test_update_rapor_schedule(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        schedule = RaporScheduleFactory.create(periyod="gunluk")

        dto = RaporScheduleUpdate(periyod="haftalik")
        result = update_rapor_schedule(db_session, schedule.id, dto, kullanici.id)

        assert result.periyod == "haftalik"

    def test_update_rapor_schedule_bulunamadi(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        dto = RaporScheduleUpdate(periyod="aylik")

        result = update_rapor_schedule(db_session, 99999, dto, kullanici.id)

        assert result is None

    def test_delete_rapor_schedule(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        schedule = RaporScheduleFactory.create()

        result = delete_rapor_schedule(db_session, schedule.id, kullanici.id)

        assert result is True

    def test_delete_rapor_schedule_bulunamadi(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")

        result = delete_rapor_schedule(db_session, 99999, kullanici.id)

        assert result is False


# ========================
# RAPOR VERİ ÜRETİMİ TESTLERI
# ========================

class TestRaporVerileri:

    def test_get_stok_raporu_verileri(self, db_session):
        UrunFactory.create(isim="Urun A")
        UrunFactory.create(isim="Urun B")

        result = get_stok_raporu_verileri(db_session)

        assert len(result) == 2

    def test_get_stok_raporu_urun_filtre(self, db_session):
        urun = UrunFactory.create(isim="Tek Urun")
        UrunFactory.create(isim="Diger")

        result = get_stok_raporu_verileri(db_session, urun_id=urun.id)

        assert len(result) == 1

    def test_get_kritik_stok_raporu(self, db_session):
        """Min stok altındaki ürünler listelenmeli."""
        UrunFactory.create(isim="Kritik", min_stok=100)  # stok=0, min_stok=100
        urun_normal = UrunFactory.create(isim="Normal", min_stok=5)
        lot = LotFactory.create(urun=urun_normal)
        PaletFactory.create(lot=lot, koli_adedi=50)

        db_session.expire_all()
        result = get_kritik_stok_raporu(db_session)

        isimler = [r.isim for r in result]
        assert "Kritik" in isimler

    def test_get_depo_doluluk(self, db_session):
        raf = RafFactory.create(kapasite=100)
        lot = LotFactory.create()
        PaletFactory.create(lot=lot, raf=raf)
        PaletFactory.create(lot=lot, raf=raf)

        result = get_depo_doluluk(db_session)

        assert len(result) >= 1
        raf_data = next(r for r in result if r["raf_id"] == raf.id)
        assert raf_data["dolu"] == 2
        assert raf_data["kapasite"] == 100
        assert raf_data["doluluk_yuzde"] == 2.0

    def test_get_depo_doluluk_bos_raf(self, db_session):
        """Boş raf doluluk %0 olmalı."""
        RafFactory.create(kapasite=50)

        result = get_depo_doluluk(db_session)

        assert len(result) == 1
        assert result[0]["dolu"] == 0
        assert result[0]["doluluk_yuzde"] == 0

    def test_get_abc_analiz(self, db_session):
        """ABC analizi: kümülatif %70 A, %90 B, kalan C."""
        urun_a = UrunFactory.create(isim="Urun A")
        urun_b = UrunFactory.create(isim="Urun B")
        urun_c = UrunFactory.create(isim="Urun C")

        siparis = SiparisFactory.create(durum="Bekleme")
        # Kümülatif: A=70/100=70%→A, B=90/100=90%→B, C=100/100→C
        SiparisKalemiFactory.create(siparis=siparis, urun=urun_a, miktar=70, birim_fiyat=1.0, toplam=70.0)
        SiparisKalemiFactory.create(siparis=siparis, urun=urun_b, miktar=20, birim_fiyat=1.0, toplam=20.0)
        SiparisKalemiFactory.create(siparis=siparis, urun=urun_c, miktar=10, birim_fiyat=1.0, toplam=10.0)

        result = get_abc_analiz(db_session)

        assert len(result) == 3
        siniflar = {r["urun_isim"]: r["sinif"] for r in result}
        assert siniflar["Urun A"] == "A"
        assert siniflar["Urun B"] == "B"
        assert siniflar["Urun C"] == "C"

    def test_get_abc_analiz_bos(self, db_session):
        """Sipariş yoksa boş liste dönmeli."""
        result = get_abc_analiz(db_session)
        assert result == []

    def test_get_skt_raporu(self, db_session):
        """SKT'si yaklaşan lotlar listelenmeli."""
        urun = UrunFactory.create()
        lot = LotFactory.create(
            urun=urun,
            son_kullanma_tarihi=date.today() + timedelta(days=10),
        )
        PaletFactory.create(lot=lot, koli_adedi=20)

        result = get_skt_raporu(db_session, gun=30)

        assert len(result) >= 1
        assert result[0].lot_no == lot.lot_no
