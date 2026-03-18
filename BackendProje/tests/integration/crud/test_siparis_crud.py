"""Integration testler: Sipariş CRUD — gerçek MySQL DB ile."""

import pytest
from datetime import date, timedelta
from crud.siparis_crud import (
    generate_siparis_no,
    get_siparisler,
    get_siparis,
    create_siparis,
    update_siparis,
    delete_siparis,
)
from schemas import SiparisCreate, SiparisUpdate, SiparisKalemiCreate
from models import SistemLog
from tests.factories import (
    SiparisFactory,
    KullaniciFactory,
    UrunFactory,
)

pytestmark = pytest.mark.integration


class TestSiparisCrud:

    def test_generate_siparis_no_ilk(self, db_session):
        """Yıl içinde ilk sipariş: SIP-YYYY-0001."""
        no = generate_siparis_no(db_session)
        from datetime import datetime
        yil = datetime.utcnow().year
        assert no == f"SIP-{yil}-0001"

    def test_generate_siparis_no_ardisik(self, db_session):
        """Mevcut sipariş varsa bir sonraki numara üretilmeli."""
        SiparisFactory.create()  # SIP-2026-0001
        no = generate_siparis_no(db_session)
        assert no.endswith("-0002")

    def test_create_siparis_tek_kalem(self, db_session):
        """Tek kalemli sipariş oluşturma + KDV hesabı."""
        kullanici = KullaniciFactory.create(rol="admin")
        urun = UrunFactory.create(fiyat=100.0)

        dto = SiparisCreate(
            musteri_adi="Test Musteri",
            teslimat_adresi="Istanbul",
            teslimat_tarihi=date.today() + timedelta(days=5),
            kalemler=[
                SiparisKalemiCreate(
                    urun_id=urun.id,
                    miktar=10,
                    birim_fiyat=100.0,
                    kdv_orani=18.0,
                )
            ],
        )

        siparis = create_siparis(db_session, dto, kullanici.id)

        assert siparis.id is not None
        assert siparis.siparis_no is not None
        assert siparis.musteri_adi == "Test Musteri"
        assert siparis.top_miktar == 10
        # KDV: 10 * 100 * 1.18 = 1180.0
        assert abs(siparis.top_tutar - 1180.0) < 0.01
        assert len(siparis.kalemler) == 1
        assert abs(siparis.kalemler[0].toplam - 1180.0) < 0.01

    def test_create_siparis_cok_kalem(self, db_session):
        """Birden fazla kalem ile sipariş oluşturma."""
        kullanici = KullaniciFactory.create(rol="admin")
        urun1 = UrunFactory.create()
        urun2 = UrunFactory.create()

        dto = SiparisCreate(
            musteri_adi="Coklu Musteri",
            teslimat_adresi="Ankara",
            teslimat_tarihi=date.today() + timedelta(days=3),
            kalemler=[
                SiparisKalemiCreate(urun_id=urun1.id, miktar=5, birim_fiyat=50.0, kdv_orani=18.0),
                SiparisKalemiCreate(urun_id=urun2.id, miktar=3, birim_fiyat=200.0, kdv_orani=8.0),
            ],
        )

        siparis = create_siparis(db_session, dto, kullanici.id)

        assert siparis.top_miktar == 8
        assert len(siparis.kalemler) == 2
        # 5*50*1.18 + 3*200*1.08 = 295 + 648 = 943
        assert abs(siparis.top_tutar - 943.0) < 0.01

    def test_create_siparis_sistem_log(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        urun = UrunFactory.create()

        dto = SiparisCreate(
            musteri_adi="Log Musteri",
            teslimat_adresi="Izmir",
            teslimat_tarihi=date.today() + timedelta(days=3),
            kalemler=[
                SiparisKalemiCreate(urun_id=urun.id, miktar=1, birim_fiyat=10.0),
            ],
        )

        create_siparis(db_session, dto, kullanici.id)

        log = db_session.query(SistemLog).filter(
            SistemLog.modul == "Sipariş Yönetimi",
            SistemLog.islem_tipi == "CREATE",
        ).first()
        assert log is not None
        assert "Log Musteri" in log.detay

    def test_get_siparisler(self, db_session):
        SiparisFactory.create(musteri_adi="A")
        SiparisFactory.create(musteri_adi="B")

        result = get_siparisler(db_session)

        assert len(result) == 2

    def test_get_siparisler_durum_filtre(self, db_session):
        SiparisFactory.create(durum="Bekleme")
        SiparisFactory.create(durum="Hazirlaniyor")

        result = get_siparisler(db_session, durum="Bekleme")

        assert len(result) == 1
        assert result[0].durum == "Bekleme"

    def test_get_siparisler_arama(self, db_session):
        SiparisFactory.create(musteri_adi="Ahmet Yilmaz")
        SiparisFactory.create(musteri_adi="Mehmet Demir")

        result = get_siparisler(db_session, arama="Ahmet")

        assert len(result) == 1
        assert result[0].musteri_adi == "Ahmet Yilmaz"

    def test_get_siparis_by_id(self, db_session):
        siparis = SiparisFactory.create()

        result = get_siparis(db_session, siparis.id)

        assert result is not None
        assert result.id == siparis.id

    def test_get_siparis_bulunamadi(self, db_session):
        result = get_siparis(db_session, 99999)
        assert result is None

    def test_update_siparis_durum(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        siparis = SiparisFactory.create(durum="Bekleme")

        dto = SiparisUpdate(durum="Hazirlaniyor")
        result = update_siparis(db_session, siparis.id, dto, kullanici.id)

        assert result.durum == "Hazirlaniyor"

    def test_update_siparis_bulunamadi(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        dto = SiparisUpdate(durum="X")

        result = update_siparis(db_session, 99999, dto, kullanici.id)

        assert result is None

    def test_delete_siparis_soft(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        siparis = SiparisFactory.create()

        result = delete_siparis(db_session, siparis.id, kullanici.id)

        assert result is True
        deleted = get_siparis(db_session, siparis.id)
        assert deleted.aktif is False

    def test_delete_siparis_bulunamadi(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")

        result = delete_siparis(db_session, 99999, kullanici.id)

        assert result is False
