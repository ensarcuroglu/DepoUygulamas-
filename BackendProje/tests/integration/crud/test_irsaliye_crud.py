"""Integration testler: İrsaliye CRUD — gerçek MySQL DB ile."""

import pytest
from datetime import date, datetime
from crud.irsaliye_crud import (
    generate_irsaliye_no,
    get_irsaliyeler,
    get_irsaliye,
    create_irsaliye,
    update_irsaliye,
)
from schemas import IrsaliyeCreate, IrsaliyeUpdate
from models import SistemLog, StokHareketi
from tests.factories import (
    SiparisFactory,
    SiparisKalemiFactory,
    SevkiyatPlaniFactory,
    IrsaliyeFactory,
    KullaniciFactory,
    UrunFactory,
    LotFactory,
    PaletFactory,
)

pytestmark = pytest.mark.integration


class TestIrsaliyeCrud:

    def test_generate_irsaliye_no_ilk(self, db_session):
        no = generate_irsaliye_no(db_session)
        yil = datetime.utcnow().year
        assert no == f"IRS-{yil}-0001"

    def test_generate_irsaliye_no_ardisik(self, db_session):
        yil = datetime.utcnow().year
        IrsaliyeFactory.create(irsaliye_no=f"IRS-{yil}-0050")
        no = generate_irsaliye_no(db_session)
        assert no == f"IRS-{yil}-0051"

    def test_create_irsaliye_basit(self, db_session):
        """Sevkiyat planı olmayan sipariş için irsaliye oluşturma."""
        kullanici = KullaniciFactory.create(rol="admin")
        siparis = SiparisFactory.create()

        dto = IrsaliyeCreate(
            siparis_id=siparis.id,
            irsaliye_tarihi=date.today(),
            tir_plaka="34 ABC 001",
            sofor_adi="Ahmet",
        )

        result = create_irsaliye(db_session, dto, kullanici.id)

        assert result.id is not None
        assert result.irsaliye_no is not None
        assert result.siparis_id == siparis.id
        assert result.durum == "Taslak"

    def test_create_irsaliye_stok_cikisi(self, db_session):
        """Sevkiyat planı yoksa irsaliye oluşturulurken stok çıkışı yapılmalı."""
        kullanici = KullaniciFactory.create(rol="admin")
        urun = UrunFactory.create()
        lot = LotFactory.create(urun=urun)
        PaletFactory.create(lot=lot, koli_adedi=100)

        siparis = SiparisFactory.create()
        SiparisKalemiFactory.create(siparis=siparis, urun=urun, miktar=15, birim_fiyat=50.0)

        dto = IrsaliyeCreate(
            siparis_id=siparis.id,
            irsaliye_tarihi=date.today(),
        )
        create_irsaliye(db_session, dto, kullanici.id)

        cikis = db_session.query(StokHareketi).filter(
            StokHareketi.hareket_tipi == "cikis",
            StokHareketi.urun_id == urun.id,
        ).first()
        assert cikis is not None
        assert cikis.miktar == 15

    def test_create_irsaliye_sevkiyat_varsa_stok_cikisi_yapilmaz(self, db_session):
        """Sevkiyat planı Yukleniyor ise irsaliye stok çıkışı yapmamalı (idempotans)."""
        kullanici = KullaniciFactory.create(rol="admin")
        urun = UrunFactory.create()
        lot = LotFactory.create(urun=urun)
        PaletFactory.create(lot=lot, koli_adedi=100)

        siparis = SiparisFactory.create()
        SiparisKalemiFactory.create(siparis=siparis, urun=urun, miktar=10, birim_fiyat=50.0)
        SevkiyatPlaniFactory.create(siparis=siparis, durum="Yukleniyor")

        dto = IrsaliyeCreate(
            siparis_id=siparis.id,
            irsaliye_tarihi=date.today(),
        )
        create_irsaliye(db_session, dto, kullanici.id)

        # İrsaliye oluşturulunca ek stok çıkışı olmamalı
        cikis_sayisi = db_session.query(StokHareketi).filter(
            StokHareketi.hareket_tipi == "cikis",
            StokHareketi.urun_id == urun.id,
        ).count()
        assert cikis_sayisi == 0

    def test_create_irsaliye_sistem_log(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        siparis = SiparisFactory.create()

        dto = IrsaliyeCreate(
            siparis_id=siparis.id,
            irsaliye_tarihi=date.today(),
        )
        create_irsaliye(db_session, dto, kullanici.id)

        log = db_session.query(SistemLog).filter(
            SistemLog.modul == "İrsaliye Yönetimi",
            SistemLog.islem_tipi == "CREATE",
        ).first()
        assert log is not None

    def test_get_irsaliyeler(self, db_session):
        IrsaliyeFactory.create()
        IrsaliyeFactory.create()

        result = get_irsaliyeler(db_session)

        assert len(result) == 2

    def test_get_irsaliyeler_durum_filtre(self, db_session):
        IrsaliyeFactory.create(durum="Taslak")
        IrsaliyeFactory.create(durum="Kesildi")

        result = get_irsaliyeler(db_session, durum="Taslak")

        assert len(result) == 1

    def test_get_irsaliye_by_id(self, db_session):
        irs = IrsaliyeFactory.create()

        result = get_irsaliye(db_session, irs.id)

        assert result is not None
        assert result.id == irs.id

    def test_get_irsaliye_bulunamadi(self, db_session):
        result = get_irsaliye(db_session, 99999)
        assert result is None

    def test_update_irsaliye_durum(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        irs = IrsaliyeFactory.create(durum="Taslak")

        dto = IrsaliyeUpdate(durum="Kesildi")
        result = update_irsaliye(db_session, irs.id, dto, kullanici.id)

        assert result.durum == "Kesildi"

    def test_update_irsaliye_bulunamadi(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        dto = IrsaliyeUpdate(durum="X")

        result = update_irsaliye(db_session, 99999, dto, kullanici.id)

        assert result is None
