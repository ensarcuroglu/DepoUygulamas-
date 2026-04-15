"""
Integration testler: Faz 5 — İzlenebilirlik ve Eşzamanlı Numara Üretimi.

Kapsam:
- StokCikisDomainService palet-bazlı hareket kaydı (lot_id/palet_id/raf_id dolu).
- siparis_icin_irsaliye_no_guncelle — çıkış hareketlerini irsaliye_no ile backfill.
- Eşzamanlı sipariş numarası üretimi — unique constraint altında davranış.
- Eşzamanlı irsaliye numarası üretimi — unique constraint altında davranış.
"""

import threading
from datetime import date

import pytest
from sqlalchemy.orm import sessionmaker, Session

from models import (
    StokHareketi as StokHareketiORM,
    Siparis as SiparisORM,
    Irsaliye as IrsaliyeORM,
)
from app.core.entities.stok_hareketi import HareketTipi
from app.infrastructure.persistence.repositories import (
    SqlAlchemyPaletRepository,
    SqlAlchemyStokHareketiRepository,
    SqlAlchemySistemLogRepository,
    SqlAlchemySiparisRepository,
    SqlAlchemyIrsaliyeRepository,
)
from app.core.services.stok_cikis_domain_service import StokCikisDomainService

from tests.factories import (
    DepoFactory, RafFactory, MarkaFactory, KategoriFactory,
    UrunFactory, LotFactory, PaletFactory, KullaniciFactory,
    SiparisFactory, SiparisKalemiFactory,
)

pytestmark = pytest.mark.integration


# ═══════════════════════════════════════════
# İZLENEBİLİRLİK — palet-bazlı hareket kaydı
# ═══════════════════════════════════════════

class TestPaletBazliHareketKaydi:
    """StokCikisDomainService gerçek palet/lot/raf ID'lerini hareket kaydına yazar."""

    def test_tek_palet_cikisi_lot_palet_raf_id_doldurur(self, db_session):
        depo = DepoFactory.create()
        raf = RafFactory.create(depo=depo, kod="R-01-A")
        marka = MarkaFactory.create()
        kategori = KategoriFactory.create()
        urun = UrunFactory.create(marka=marka, kategori=kategori)
        lot = LotFactory.create(urun=urun, lot_no="LOT-CIK-001")
        palet = PaletFactory.create(lot=lot, raf=raf, koli_adedi=20)
        kullanici = KullaniciFactory.create(kullanici_adi="cikis_tester", rol="lojistik")

        siparis = SiparisFactory.create(olusturan_kullanici=kullanici)
        kalem = SiparisKalemiFactory.create(siparis=siparis, urun=urun, miktar=5)
        db_session.commit()

        service = StokCikisDomainService(
            palet_repo=SqlAlchemyPaletRepository(db_session),
            hareket_repo=SqlAlchemyStokHareketiRepository(db_session),
            log_repo=SqlAlchemySistemLogRepository(db_session),
        )

        service.siparis_bazli_stok_cikisi(
            kalemler=[kalem],
            siparis_no=siparis.siparis_no,
            kullanici_id=kullanici.id,
        )
        db_session.commit()

        hareketler = (
            db_session.query(StokHareketiORM)
            .filter(StokHareketiORM.siparis_no == siparis.siparis_no)
            .all()
        )
        assert len(hareketler) == 1
        h = hareketler[0]
        assert h.hareket_tipi == HareketTipi.CIKIS
        assert h.urun_id == urun.id
        assert h.lot_id == lot.id
        assert h.palet_id == palet.id
        assert h.raf_id == raf.id
        assert h.miktar == 5
        assert h.irsaliye_no is None

    def test_coklu_palet_cikisi_her_palet_icin_ayri_hareket(self, db_session):
        depo = DepoFactory.create()
        raf1 = RafFactory.create(depo=depo, kod="R-02-A")
        raf2 = RafFactory.create(depo=depo, kod="R-02-B")
        marka = MarkaFactory.create()
        kategori = KategoriFactory.create()
        urun = UrunFactory.create(marka=marka, kategori=kategori)
        lot = LotFactory.create(urun=urun, lot_no="LOT-CIK-002", son_kullanma_tarihi=date(2027, 1, 1))
        palet1 = PaletFactory.create(lot=lot, raf=raf1, koli_adedi=4)
        palet2 = PaletFactory.create(lot=lot, raf=raf2, koli_adedi=10)
        kullanici = KullaniciFactory.create(kullanici_adi="cikis_multi", rol="lojistik")

        siparis = SiparisFactory.create(olusturan_kullanici=kullanici)
        kalem = SiparisKalemiFactory.create(siparis=siparis, urun=urun, miktar=9)
        db_session.commit()

        service = StokCikisDomainService(
            palet_repo=SqlAlchemyPaletRepository(db_session),
            hareket_repo=SqlAlchemyStokHareketiRepository(db_session),
            log_repo=SqlAlchemySistemLogRepository(db_session),
        )

        service.siparis_bazli_stok_cikisi(
            kalemler=[kalem],
            siparis_no=siparis.siparis_no,
            kullanici_id=kullanici.id,
        )
        db_session.commit()

        hareketler = (
            db_session.query(StokHareketiORM)
            .filter(StokHareketiORM.siparis_no == siparis.siparis_no)
            .order_by(StokHareketiORM.id.asc())
            .all()
        )
        assert len(hareketler) == 2
        assert (hareketler[0].palet_id, hareketler[0].miktar) == (palet1.id, 4)
        assert (hareketler[1].palet_id, hareketler[1].miktar) == (palet2.id, 5)
        assert all(h.raf_id in {raf1.id, raf2.id} for h in hareketler)
        assert all(h.lot_id == lot.id for h in hareketler)


# ═══════════════════════════════════════════
# İZLENEBİLİRLİK — irsaliye_no backfill
# ═══════════════════════════════════════════

class TestIrsaliyeNoBackfill:
    """İrsaliye numarası bekleyen çıkış hareketlerine geri yazılır."""

    def test_backfill_acik_cikis_hareketlerini_gunceller(self, db_session):
        depo = DepoFactory.create()
        raf = RafFactory.create(depo=depo, kod="R-03-A")
        marka = MarkaFactory.create()
        kategori = KategoriFactory.create()
        urun = UrunFactory.create(marka=marka, kategori=kategori)
        lot = LotFactory.create(urun=urun, lot_no="LOT-BF-001")
        palet = PaletFactory.create(lot=lot, raf=raf, koli_adedi=10)
        kullanici = KullaniciFactory.create(kullanici_adi="bf_tester", rol="lojistik")

        siparis = SiparisFactory.create(olusturan_kullanici=kullanici)
        kalem = SiparisKalemiFactory.create(siparis=siparis, urun=urun, miktar=3)
        db_session.commit()

        hareket_repo = SqlAlchemyStokHareketiRepository(db_session)
        service = StokCikisDomainService(
            palet_repo=SqlAlchemyPaletRepository(db_session),
            hareket_repo=hareket_repo,
            log_repo=SqlAlchemySistemLogRepository(db_session),
        )

        service.siparis_bazli_stok_cikisi(
            kalemler=[kalem], siparis_no=siparis.siparis_no, kullanici_id=kullanici.id,
        )
        db_session.commit()

        etkilenen = hareket_repo.siparis_icin_irsaliye_no_guncelle(
            siparis.siparis_no, "IRS-2026-0777",
        )
        assert etkilenen == 1

        hareket = (
            db_session.query(StokHareketiORM)
            .filter(StokHareketiORM.siparis_no == siparis.siparis_no)
            .one()
        )
        assert hareket.irsaliye_no == "IRS-2026-0777"
        # palet_id kullanılmış
        assert hareket.palet_id == palet.id

    def test_backfill_zaten_irsaliye_nosu_olan_hareketi_ezmez(self, db_session):
        depo = DepoFactory.create()
        raf = RafFactory.create(depo=depo, kod="R-04-A")
        marka = MarkaFactory.create()
        kategori = KategoriFactory.create()
        urun = UrunFactory.create(marka=marka, kategori=kategori)
        lot = LotFactory.create(urun=urun, lot_no="LOT-BF-002")
        PaletFactory.create(lot=lot, raf=raf, koli_adedi=10)
        kullanici = KullaniciFactory.create(kullanici_adi="bf_idemp", rol="lojistik")

        siparis = SiparisFactory.create(olusturan_kullanici=kullanici)
        kalem = SiparisKalemiFactory.create(siparis=siparis, urun=urun, miktar=2)
        db_session.commit()

        hareket_repo = SqlAlchemyStokHareketiRepository(db_session)
        StokCikisDomainService(
            palet_repo=SqlAlchemyPaletRepository(db_session),
            hareket_repo=hareket_repo,
            log_repo=SqlAlchemySistemLogRepository(db_session),
        ).siparis_bazli_stok_cikisi(
            kalemler=[kalem], siparis_no=siparis.siparis_no, kullanici_id=kullanici.id,
        )
        db_session.commit()

        hareket_repo.siparis_icin_irsaliye_no_guncelle(siparis.siparis_no, "IRS-FIRST")
        ikinci_etki = hareket_repo.siparis_icin_irsaliye_no_guncelle(siparis.siparis_no, "IRS-SECOND")
        assert ikinci_etki == 0

        hareket = (
            db_session.query(StokHareketiORM)
            .filter(StokHareketiORM.siparis_no == siparis.siparis_no)
            .one()
        )
        assert hareket.irsaliye_no == "IRS-FIRST"


# ═══════════════════════════════════════════
# EŞZAMANLI NUMARA ÜRETİMİ
# ═══════════════════════════════════════════

def _yeni_session(engine) -> Session:
    return sessionmaker(bind=engine)()


def _paralel_calistir(engine, worker_fn, thread_sayisi: int):
    sonuclar = [None] * thread_sayisi
    barrier = threading.Barrier(thread_sayisi)

    def _run(idx):
        session = _yeni_session(engine)
        try:
            barrier.wait(timeout=10)
            sonuclar[idx] = ("ok", worker_fn(session))
        except Exception as e:
            session.rollback()
            sonuclar[idx] = ("err", f"{type(e).__name__}: {e}")
        finally:
            session.close()

    threads = [threading.Thread(target=_run, args=(i,)) for i in range(thread_sayisi)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    return sonuclar


class TestEszamanliNumaraUretimi:
    """Sipariş ve irsaliye numaraları eşzamanlı üretildiğinde unique constraint
    ihlali oluşsa dahi veritabanında tekilleştirme korunmalı."""

    def test_eszamanli_siparis_numarasi_uretimi_tekrarlanmaz(self, engine, db_session):
        from datetime import datetime as _dt
        kullanici = KullaniciFactory.create(kullanici_adi="conc_siparis", rol="admin")
        db_session.commit()
        kullanici_id = kullanici.id
        yil = _dt.utcnow().year

        THREAD = 5

        def worker(session):
            repo = SqlAlchemySiparisRepository(session)
            siparis_no = repo.sonraki_siparis_no()
            orm = SiparisORM(
                siparis_no=siparis_no,
                musteri_adi="Conc Musteri",
                teslimat_adresi="Test Adres",
                teslimat_tarihi=date.today(),
                durum="Bekleme",
                top_miktar=0,
                top_tutar=0.0,
                olusturan_kullanici_id=kullanici_id,
                aktif=True,
            )
            session.add(orm)
            session.commit()
            return siparis_no

        sonuclar = _paralel_calistir(engine, worker, THREAD)

        basarili_nolar = [s[1] for s in sonuclar if s and s[0] == "ok"]
        # En az 1 başarılı olmalı.
        assert len(basarili_nolar) >= 1
        # DB'deki tüm siparişler tekil numaraya sahip.
        kontrol = _yeni_session(engine)
        try:
            kayitlar = kontrol.query(SiparisORM).filter(
                SiparisORM.siparis_no.like(f"SIP-{yil}-%")
            ).all()
            nolar = [k.siparis_no for k in kayitlar]
            assert len(nolar) == len(set(nolar)), f"Mükerrer numara tespit edildi: {nolar}"
        finally:
            kontrol.close()

    def test_eszamanli_irsaliye_numarasi_uretimi_tekrarlanmaz(self, engine, db_session):
        from datetime import datetime as _dt
        kullanici = KullaniciFactory.create(kullanici_adi="conc_irsaliye", rol="admin")
        siparis = SiparisFactory.create(olusturan_kullanici=kullanici)
        db_session.commit()
        siparis_id = siparis.id
        yil = _dt.utcnow().year

        THREAD = 5

        def worker(session):
            repo = SqlAlchemyIrsaliyeRepository(session)
            irsaliye_no = repo.sonraki_irsaliye_no()
            orm = IrsaliyeORM(
                siparis_id=siparis_id,
                irsaliye_no=irsaliye_no,
                irsaliye_tarihi=date.today(),
                belge_turu="SevkIrsaliyesi",
                durum="Taslak",
            )
            session.add(orm)
            session.commit()
            return irsaliye_no

        sonuclar = _paralel_calistir(engine, worker, THREAD)

        basarili_nolar = [s[1] for s in sonuclar if s and s[0] == "ok"]
        assert len(basarili_nolar) >= 1
        kontrol = _yeni_session(engine)
        try:
            kayitlar = kontrol.query(IrsaliyeORM).filter(
                IrsaliyeORM.irsaliye_no.like(f"IRS-{yil}-%")
            ).all()
            nolar = [k.irsaliye_no for k in kayitlar]
            assert len(nolar) == len(set(nolar)), f"Mükerrer numara tespit edildi: {nolar}"
        finally:
            kontrol.close()
