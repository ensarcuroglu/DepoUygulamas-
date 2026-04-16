"""
Phase 2 concurrency tests.

These tests verify the production use case paths on a real MySQL database
with separate SQLAlchemy sessions per thread.
"""

import threading
import time
from datetime import date

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.application.use_cases.palet_rezervasyonu_use_cases import RezervasyonBaslatUseCase
from app.application.use_cases.toplama_gorevi_use_cases import SiradanGorevAlUseCase
from app.core.entities.palet_rezervasyonu import RezervasyonDurum
from app.core.entities.toplama_gorevi import ToplamaGoreviDurum
from app.core.services.fefo_secim_servisi import FEFOSecimServisi
from app.infrastructure.persistence.repositories.sa_palet_rezervasyonu_repository import (
    SqlAlchemyPaletRezervasyonuRepository,
)
from app.infrastructure.persistence.repositories.sa_palet_repository import (
    SqlAlchemyPaletRepository,
)
from app.infrastructure.persistence.repositories.sa_siparis_repository import SqlAlchemySiparisRepository
from app.infrastructure.persistence.repositories.sa_sistem_log_repository import (
    SqlAlchemySistemLogRepository,
)
from app.infrastructure.persistence.repositories.sa_toplama_gorevi_repository import (
    SqlAlchemyToplamaGoreviRepository,
)
from models import PaletRezervasyonu as PaletRezervasyonuORM
from models import SevkiyatKalemi as SevkiyatKalemiORM
from models import ToplamaGorevi as ToplamaGoreviORM
from tests.factories import (
    DepoFactory,
    KullaniciFactory,
    LotFactory,
    PaletFactory,
    RafFactory,
    SevkiyatPlaniFactory,
    SiparisFactory,
    SiparisKalemiFactory,
    UrunFactory,
)

pytestmark = [pytest.mark.integration, pytest.mark.concurrency]


def _yeni_session(engine) -> Session:
    # READ COMMITTED avoids InnoDB gap-lock behavior that can starve SKIP LOCKED
    # dequeue tests when multiple rows share the same waiting queue.
    session_factory = sessionmaker(
        bind=engine.execution_options(isolation_level="READ COMMITTED")
    )
    return session_factory()


def _thread_worker(engine, worker_fn, sonuclar, index, barrier=None):
    session = _yeni_session(engine)
    try:
        if barrier is not None:
            barrier.wait(timeout=10)
        sonuclar[index] = ("basarili", worker_fn(session))
    except Exception as exc:  # pragma: no cover
        session.rollback()
        sonuclar[index] = ("hata", f"{type(exc).__name__}: {exc}")
    finally:
        session.close()


def _calistir_paralel(engine, worker_fn, thread_sayisi):
    sonuclar = [None] * thread_sayisi
    barrier = threading.Barrier(thread_sayisi)
    threads = [
        threading.Thread(
            target=_thread_worker,
            args=(engine, worker_fn, sonuclar, index, barrier),
        )
        for index in range(thread_sayisi)
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    return sonuclar


class _SlowLockingToplamaGoreviRepository(SqlAlchemyToplamaGoreviRepository):
    def __init__(self, db: Session, delay_seconds: float = 0.05):
        super().__init__(db)
        self._delay_seconds = delay_seconds

    def getir_next_bekleyen(self, depo_id=None, with_lock=False):
        gorev = super().getir_next_bekleyen(depo_id=depo_id, with_lock=with_lock)
        if gorev is not None and with_lock:
            time.sleep(self._delay_seconds)
        return gorev


class _SlowLockingPaletRepository(SqlAlchemyPaletRepository):
    def __init__(self, db: Session, delay_seconds: float = 0.08):
        super().__init__(db)
        self._delay_seconds = delay_seconds

    def getir_fifo_sirayla_kilitli(self, urun_id: int):
        paletler = super().getir_fifo_sirayla_kilitli(urun_id)
        if paletler:
            time.sleep(self._delay_seconds)
        return paletler


def _seed_gorev_havuzu(db_session, gorev_sayisi: int):
    depo = DepoFactory.create()
    raf = RafFactory.create(depo=depo)
    kullanici = KullaniciFactory.create(rol="depocu", depo_id=depo.id)
    urun = UrunFactory.create()
    lot = LotFactory.create(urun=urun)

    gorevler = []
    for sira_no in range(1, gorev_sayisi + 1):
        palet = PaletFactory.create(lot=lot, raf=raf)
        siparis = SiparisFactory.create(durum="Hazirlaniyor")
        sevkiyat = SevkiyatPlaniFactory.create(siparis=siparis)
        gorev = ToplamaGoreviORM(
            sevkiyat_id=sevkiyat.id,
            palet_id=palet.id,
            lot_id=lot.id,
            urun_id=urun.id,
            depo_id=depo.id,
            durum=ToplamaGoreviDurum.BEKLEMEDE,
            sira_no=sira_no,
        )
        db_session.add(gorev)
        gorevler.append(gorev)

    db_session.commit()
    for gorev in gorevler:
        db_session.refresh(gorev)

    return depo.id, kullanici.id, [gorev.id for gorev in gorevler]


def _seed_rezervasyon_yarisi(db_session):
    depo = DepoFactory.create()
    raf = RafFactory.create(depo=depo)
    kullanici = KullaniciFactory.create(rol="admin")
    urun = UrunFactory.create()

    lot1 = LotFactory.create(
        urun=urun,
        uretim_tarihi=date(2026, 1, 1),
        son_kullanma_tarihi=date(2026, 6, 1),
    )
    lot2 = LotFactory.create(
        urun=urun,
        uretim_tarihi=date(2026, 2, 1),
        son_kullanma_tarihi=date(2026, 7, 1),
    )
    palet1 = PaletFactory.create(lot=lot1, raf=raf, koli_adedi=10)
    palet2 = PaletFactory.create(lot=lot2, raf=raf, koli_adedi=10)

    siparis1 = SiparisFactory.create(durum="Hazirlaniyor")
    siparis2 = SiparisFactory.create(durum="Hazirlaniyor")
    kalem1 = SiparisKalemiFactory.create(siparis=siparis1, urun=urun, miktar=5)
    kalem2 = SiparisKalemiFactory.create(siparis=siparis2, urun=urun, miktar=5)
    sevkiyat1 = SevkiyatPlaniFactory.create(siparis=siparis1)
    sevkiyat2 = SevkiyatPlaniFactory.create(siparis=siparis2)

    # Rezervasyon use case currently carries siparis kalemi IDs into the
    # sevkiyat_kalemi_id field, so the FK target must exist in the test setup.
    db_session.add_all(
        [
            SevkiyatKalemiORM(
                id=kalem1.id,
                sevkiyat_id=sevkiyat1.id,
                siparis_kalemi_id=kalem1.id,
                urun_id=urun.id,
                miktar=kalem1.miktar,
            ),
            SevkiyatKalemiORM(
                id=kalem2.id,
                sevkiyat_id=sevkiyat2.id,
                siparis_kalemi_id=kalem2.id,
                urun_id=urun.id,
                miktar=kalem2.miktar,
            ),
        ]
    )

    db_session.commit()
    return kullanici.id, [siparis1.id, siparis2.id], [palet1.id, palet2.id]


class TestSiradanGorevAlRaceCondition:
    def test_iki_thread_farkli_gorev_alir(self, engine, db_session):
        depo_id, kullanici_id, gorev_ids = _seed_gorev_havuzu(db_session, gorev_sayisi=2)

        def worker_fn(session: Session):
            repo = _SlowLockingToplamaGoreviRepository(session)
            uc = SiradanGorevAlUseCase(repo)
            sonuc = uc.execute(kullanici_id=kullanici_id, depo_id=depo_id)
            return None if sonuc is None else sonuc.id

        sonuclar = _calistir_paralel(engine, worker_fn, thread_sayisi=2)

        basarili = [sonuc for sonuc in sonuclar if sonuc and sonuc[0] == "basarili"]
        assert len(basarili) == 2, f"Her iki thread basarili olmaliydi: {sonuclar}"

        atanan_ids = [sonuc[1] for sonuc in basarili]
        beklenen_ids = set(gorev_ids)

        assert len(atanan_ids) == 2
        assert len(set(atanan_ids)) == 2, f"Ayni gorev iki kez atandi: {atanan_ids}"
        assert set(atanan_ids) == beklenen_ids

        kontrol = _yeni_session(engine)
        try:
            db_gorevler = (
                kontrol.query(ToplamaGoreviORM)
                .filter(ToplamaGoreviORM.id.in_(beklenen_ids))
                .all()
            )
            assert len(db_gorevler) == 2
            assert {gorev.durum for gorev in db_gorevler} == {ToplamaGoreviDurum.ATANDI}
            assert {gorev.atanan_kullanici_id for gorev in db_gorevler} == {kullanici_id}
        finally:
            kontrol.close()

    def test_tek_gorev_varken_ikinci_thread_none_alir(self, engine, db_session):
        depo_id, kullanici_id, gorev_ids = _seed_gorev_havuzu(db_session, gorev_sayisi=1)
        gorev_id = gorev_ids[0]

        def worker_fn(session: Session):
            repo = _SlowLockingToplamaGoreviRepository(session)
            uc = SiradanGorevAlUseCase(repo)
            sonuc = uc.execute(kullanici_id=kullanici_id, depo_id=depo_id)
            return None if sonuc is None else sonuc.id

        sonuclar = _calistir_paralel(engine, worker_fn, thread_sayisi=2)

        basarili = [sonuc for sonuc in sonuclar if sonuc and sonuc[0] == "basarili"]
        assert len(basarili) == 2, f"Threadler hata vermemeliydi: {sonuclar}"

        atanan_ids = [sonuc[1] for sonuc in basarili if sonuc[1] is not None]
        bos_sonuclar = [sonuc[1] for sonuc in basarili if sonuc[1] is None]

        assert atanan_ids == [gorev_id]
        assert len(bos_sonuclar) == 1

        kontrol = _yeni_session(engine)
        try:
            db_gorev = (
                kontrol.query(ToplamaGoreviORM)
                .filter(ToplamaGoreviORM.id == gorev_id)
                .first()
            )
            assert db_gorev is not None
            assert db_gorev.durum == ToplamaGoreviDurum.ATANDI
            assert db_gorev.atanan_kullanici_id == kullanici_id
        finally:
            kontrol.close()


class TestCiftRezervasyonEngeli:
    def test_ayni_urun_icin_iki_thread_farkli_paletler_rezerve_eder(self, engine, db_session):
        kullanici_id, siparis_ids, palet_ids = _seed_rezervasyon_yarisi(db_session)
        beklenen_palet_ids = set(palet_ids)

        def worker_factory(siparis_id: int):
            def worker_fn(session: Session):
                rezervasyon_repo = SqlAlchemyPaletRezervasyonuRepository(session)
                palet_repo = _SlowLockingPaletRepository(session)
                siparis_repo = SqlAlchemySiparisRepository(session)
                log_repo = SqlAlchemySistemLogRepository(session)
                uc = RezervasyonBaslatUseCase(
                    rezervasyon_repo=rezervasyon_repo,
                    palet_repo=palet_repo,
                    siparis_repo=siparis_repo,
                    log_repo=log_repo,
                    fefo_servisi=FEFOSecimServisi(),
                )
                sonuc = uc.execute(siparis_id=siparis_id, kullanici_id=kullanici_id)
                assert len(sonuc) == 1
                return sonuc[0].palet_id

            return worker_fn

        sonuclar = [None] * 2
        barrier = threading.Barrier(2)
        threads = [
            threading.Thread(
                target=_thread_worker,
                args=(engine, worker_factory(siparis_ids[index]), sonuclar, index, barrier),
            )
            for index in range(2)
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)

        basarili = [sonuc for sonuc in sonuclar if sonuc and sonuc[0] == "basarili"]
        assert len(basarili) == 2, f"Her iki thread basarili olmaliydi: {sonuclar}"

        rezerve_palet_ids = [sonuc[1] for sonuc in basarili]
        assert len(set(rezerve_palet_ids)) == 2, (
            f"Iki siparis ayni paleti almamaliydi: {rezerve_palet_ids}"
        )
        assert set(rezerve_palet_ids) == beklenen_palet_ids

        kontrol = _yeni_session(engine)
        try:
            db_rezervasyonlar = (
                kontrol.query(PaletRezervasyonuORM)
                .filter(
                    PaletRezervasyonuORM.siparis_id.in_(siparis_ids),
                    PaletRezervasyonuORM.durum == RezervasyonDurum.AKTIF,
                )
                .all()
            )
            assert len(db_rezervasyonlar) == 2
            assert {rez.palet_id for rez in db_rezervasyonlar} == beklenen_palet_ids
            assert {rez.siparis_id for rez in db_rezervasyonlar} == set(siparis_ids)
        finally:
            kontrol.close()
