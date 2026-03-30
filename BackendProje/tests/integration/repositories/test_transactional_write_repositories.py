"""
Integration testler: Irsaliye ve sevkiyat repository transaction davranisi.
"""

from datetime import date

import pytest

from app.core.entities.irsaliye import Irsaliye
from app.core.entities.sevkiyat_plani import SevkiyatPlani, SevkiyatDurum
from app.infrastructure.persistence.repositories.sa_irsaliye_repository import (
    SqlAlchemyIrsaliyeRepository,
)
from app.infrastructure.persistence.repositories.sa_sevkiyat_plani_repository import (
    SqlAlchemySevkiyatPlaniRepository,
)
from models import Irsaliye as IrsaliyeORM
from models import SevkiyatPlani as SevkiyatPlaniORM
from models import Siparis as SiparisORM

pytestmark = pytest.mark.integration


def _create_siparis_orm(db_session, siparis_no: str) -> SiparisORM:
    siparis = SiparisORM(
        siparis_no=siparis_no,
        musteri_adi="Test Musteri",
        teslimat_adresi="Test Adres",
        teslimat_tarihi=date(2026, 3, 30),
        durum="Bekleme",
        top_miktar=0,
        top_tutar=0.0,
        notlar="",
        olusturan_kullanici_id=None,
        aktif=True,
    )
    db_session.add(siparis)
    db_session.commit()
    db_session.refresh(siparis)
    return siparis


def _create_irsaliye_orm(db_session, siparis_id: int, irsaliye_no: str, tir_plaka: str) -> IrsaliyeORM:
    irsaliye = IrsaliyeORM(
        siparis_id=siparis_id,
        sevkiyat_id=None,
        irsaliye_no=irsaliye_no,
        irsaliye_tarihi=date(2026, 3, 30),
        belge_turu="SevkIrsaliyesi",
        tir_plaka=tir_plaka,
        sofor_adi="Test Sofor",
        durum="Taslak",
    )
    db_session.add(irsaliye)
    db_session.commit()
    db_session.refresh(irsaliye)
    return irsaliye


def _create_sevkiyat_orm(db_session, siparis_id: int, tir_plaka: str) -> SevkiyatPlaniORM:
    sevkiyat = SevkiyatPlaniORM(
        siparis_id=siparis_id,
        tir_plaka=tir_plaka,
        sofor_adi="Test Sofor",
        sofor_telefon="05550000000",
        depo_kapi="A1",
        yukleme_tarihi=date(2026, 3, 31),
        cikis_saati="08:00",
        varis_saati="16:00",
        durum=SevkiyatDurum.PLANLANDI,
        notlar="",
    )
    db_session.add(sevkiyat)
    db_session.commit()
    db_session.refresh(sevkiyat)
    return sevkiyat


class TestIrsaliyeRepositoryTransactions:

    def test_olustur_auto_commit_false_rollback_sonrasi_kalici_olmaz(self, db_session):
        siparis = _create_siparis_orm(db_session, "SIP-TX-9001")
        repo = SqlAlchemyIrsaliyeRepository(db_session)

        created = repo.olustur(
            Irsaliye(
                siparis_id=siparis.id,
                irsaliye_no="IRS-2026-9001",
                irsaliye_tarihi=date(2026, 3, 30),
                belge_turu="SevkIrsaliyesi",
                tir_plaka="34 TX 001",
                sofor_adi="Rollback Test",
            ),
            auto_commit=False,
        )

        assert created.id is not None
        db_session.rollback()

        assert repo.getir_id_ile(created.id) is None

    def test_guncelle_auto_commit_true_davranisi_korur(self, db_session):
        siparis = _create_siparis_orm(db_session, "SIP-TX-9002")
        mevcut = _create_irsaliye_orm(
            db_session,
            siparis_id=siparis.id,
            irsaliye_no="IRS-2026-9002",
            tir_plaka="34 OLD 001",
        )
        repo = SqlAlchemyIrsaliyeRepository(db_session)

        entity = repo.getir_id_ile(mevcut.id)
        entity.tir_plaka = "34 NEW 001"
        updated = repo.guncelle(entity, auto_commit=True)

        assert updated.tir_plaka == "34 NEW 001"
        db_session.expire_all()
        persisted = repo.getir_id_ile(mevcut.id)
        assert persisted.tir_plaka == "34 NEW 001"


class TestSevkiyatRepositoryTransactions:

    def test_olustur_auto_commit_false_rollback_sonrasi_kalici_olmaz(self, db_session):
        siparis = _create_siparis_orm(db_session, "SIP-TX-9003")
        repo = SqlAlchemySevkiyatPlaniRepository(db_session)

        created = repo.olustur(
            SevkiyatPlani(
                siparis_id=siparis.id,
                tir_plaka="34 TX 002",
                sofor_adi="Rollback Test",
                sofor_telefon="05550000000",
                depo_kapi="A1",
                yukleme_tarihi=date(2026, 3, 31),
                cikis_saati="08:00",
                varis_saati="16:00",
                durum=SevkiyatDurum.PLANLANDI,
                notlar="",
            ),
            auto_commit=False,
        )

        assert created.id is not None
        db_session.rollback()

        assert repo.getir_id_ile(created.id) is None

    def test_guncelle_auto_commit_true_davranisi_korur(self, db_session):
        siparis = _create_siparis_orm(db_session, "SIP-TX-9004")
        mevcut = _create_sevkiyat_orm(
            db_session,
            siparis_id=siparis.id,
            tir_plaka="34 OLD 002",
        )
        repo = SqlAlchemySevkiyatPlaniRepository(db_session)

        entity = repo.getir_id_ile(mevcut.id)
        entity.tir_plaka = "34 NEW 002"
        updated = repo.guncelle(entity, auto_commit=True)

        assert updated.tir_plaka == "34 NEW 002"
        db_session.expire_all()
        persisted = repo.getir_id_ile(mevcut.id)
        assert persisted.tir_plaka == "34 NEW 002"
