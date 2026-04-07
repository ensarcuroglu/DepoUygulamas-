"""
B5 — Eşzamanlılık (Concurrency) Testleri

Gerçek MySQL üzerinde threading + ayrı SQLAlchemy session ile:
- Çift palet girişi engeli (UNIQUE constraint)
- FIFO çıkış yarışı (SELECT FOR UPDATE kilit doğrulama)
- Kısmi çıkış eşzamanlılığı
- Deadlock dayanıklılığı

Gereksinim: MySQL 8.0+ (InnoDB), depo_db_test veritabanı.
"""

import os
import threading
import time
from datetime import date, datetime, timedelta

import pytest
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker, Session

from database import Base
from models import (
    Palet as PaletORM,
    Lot as LotORM,
    Urun as UrunORM,
    Raf as RafORM,
    Depo as DepoORM,
    Marka as MarkaORM,
    Kategori as KategoriORM,
    Kullanici as KullaniciORM,
    StokHareketi as StokHareketiORM,
    SistemLog as SistemLogORM,
)

pytestmark = [pytest.mark.integration, pytest.mark.concurrency]


# ═══════════════════════════════════════════
# HELPER: Session & Thread Yönetimi
# ═══════════════════════════════════════════

def _yeni_session(engine) -> Session:
    """Her thread için bağımsız DB session oluşturur."""
    SessionFactory = sessionmaker(bind=engine)
    return SessionFactory()


def _thread_worker(engine, worker_fn, sonuclar, index, barrier=None):
    """Thread-safe worker: kendi session'ı ile çalışır, sonucu paylaşımlı listeye yazar."""
    session = _yeni_session(engine)
    try:
        if barrier:
            barrier.wait(timeout=10)  # Tüm thread'ler aynı anda başlasın
        result = worker_fn(session)
        sonuclar[index] = ("basarili", result)
    except Exception as e:
        session.rollback()
        sonuclar[index] = ("hata", f"{type(e).__name__}: {e}")
    finally:
        session.close()


def _calistir_paralel(engine, worker_fn, thread_sayisi, barrier=None):
    """N adet thread'i eşzamanlı başlatır ve sonuçlarını toplar."""
    sonuclar = [None] * thread_sayisi
    threads = []

    if barrier is None:
        barrier = threading.Barrier(thread_sayisi)

    for i in range(thread_sayisi):
        t = threading.Thread(
            target=_thread_worker,
            args=(engine, worker_fn, sonuclar, i, barrier),
        )
        threads.append(t)

    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    return sonuclar


# ═══════════════════════════════════════════
# HELPER: Test Veri Oluşturma
# ═══════════════════════════════════════════

def _temiz_basla(session):
    """Test öncesi ilgili tabloları temizler."""
    session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    for tablo in [
        "stok_hareketleri", "sistem_loglari", "paletler", "lotlar",
        "urunler", "raflar", "depolar", "markalar", "kategoriler", "kullanicilar",
    ]:
        session.execute(text(f"TRUNCATE TABLE `{tablo}`"))
    session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    session.commit()


def _seed_temel_veri(session):
    """Tüm testlerin ihtiyacı olan temel reference veriyi yaratır.
    Returns: (depo, raf, marka, kategori, kullanici) tuple.
    """
    depo = DepoORM(isim="Test Depo Concurrency", adres="Test", aktif=True)
    session.add(depo)
    session.flush()

    raf = RafORM(depo_id=depo.id, kod="CONC-A-01-01-01", bolge="Test", kapasite=100, aktif=True)
    session.add(raf)
    session.flush()

    marka = MarkaORM(isim="Test Marka Conc", aktif=True)
    session.add(marka)
    session.flush()

    kategori = KategoriORM(isim="Test Kategori Conc", aktif=True)
    session.add(kategori)
    session.flush()

    kullanici = KullaniciORM(
        kullanici_adi="conc_test_user",
        sifre_hash="$2b$12$dummyhash000000000000000000000000000000000000000000",
        ad_soyad="Concurrency Test",
        rol="depocu",
    )
    session.add(kullanici)
    session.flush()

    session.commit()
    return depo, raf, marka, kategori, kullanici


def _olustur_urun(session, marka_id, kategori_id, isim_suffix=""):
    """Benzersiz ürün oluşturur."""
    urun = UrunORM(
        isim=f"Conc Urun {isim_suffix or datetime.utcnow().timestamp()}",
        marka_id=marka_id,
        kategori_id=kategori_id,
        barkod=f"CONC-{datetime.utcnow().timestamp()}-{isim_suffix}",
        birim="Adet",
        fiyat=10.0,
        min_stok=5,
        aktif=True,
    )
    session.add(urun)
    session.flush()
    return urun


def _olustur_lot(session, urun_id, lot_no=None, skt=None):
    """Lot oluşturur. SKT verilmezse None kalır (FIFO sıralamada sona atılır)."""
    lot = LotORM(
        urun_id=urun_id,
        lot_no=lot_no or f"LOT-CONC-{datetime.utcnow().timestamp()}",
        son_kullanma_tarihi=skt,
        aktif=True,
    )
    session.add(lot)
    session.flush()
    return lot


def _olustur_palet(session, lot_id, raf_id, palet_no, koli_adedi=10):
    """Palet oluşturur."""
    palet = PaletORM(
        lot_id=lot_id,
        raf_id=raf_id,
        palet_no=palet_no,
        koli_adedi=koli_adedi,
        aktif=True,
    )
    session.add(palet)
    session.flush()
    return palet


# ═══════════════════════════════════════════
# TEST SINIFI 1: Palet Giriş Eşzamanlılığı
# ═══════════════════════════════════════════

class TestPaletGirisEszamanlilik:
    """Aynı palet numarasıyla eşzamanlı giriş denemelerinin doğru engellendiğini test eder."""

    def test_ayni_palet_no_ile_paralel_giris_sadece_biri_basarili(self, engine, db_session):
        """2 thread aynı anda aynı palet_no ile INSERT yapar.
        UNIQUE constraint sayesinde sadece 1'i başarılı olmalı.
        """
        _temiz_basla(db_session)
        depo, raf, marka, kategori, kullanici = _seed_temel_veri(db_session)

        urun = _olustur_urun(db_session, marka.id, kategori.id, "dup-test")
        lot = _olustur_lot(db_session, urun.id, "LOT-DUP-001")
        db_session.commit()

        palet_no = "PLT-DUPLICATE-001"
        barrier = threading.Barrier(2)

        def worker_fn(session):
            palet = PaletORM(
                lot_id=lot.id,
                raf_id=raf.id,
                palet_no=palet_no,
                koli_adedi=10,
                aktif=True,
            )
            session.add(palet)
            session.commit()
            return palet.id

        sonuclar = _calistir_paralel(engine, worker_fn, 2, barrier)

        basarili = [s for s in sonuclar if s and s[0] == "basarili"]
        hatali = [s for s in sonuclar if s and s[0] == "hata"]

        assert len(basarili) == 1, f"Tam 1 thread başarılı olmalıydı, oldu: {len(basarili)}"
        assert len(hatali) == 1, f"Tam 1 thread hata almalıydı, oldu: {len(hatali)}"

        # DB'de tek kayıt olduğunu doğrula
        kontrol_session = _yeni_session(engine)
        try:
            sayac = kontrol_session.query(func.count(PaletORM.id)).filter(
                PaletORM.palet_no == palet_no
            ).scalar()
            assert sayac == 1, f"DB'de {palet_no} için {sayac} kayıt var, 1 olmalıydı"
        finally:
            kontrol_session.close()

    def test_farkli_palet_no_ile_paralel_giris_hepsi_basarili(self, engine, db_session):
        """5 thread farklı palet numaralarıyla eşzamanlı giriş yapar.
        Hepsi başarılı olmalı.
        """
        _temiz_basla(db_session)
        depo, raf, marka, kategori, kullanici = _seed_temel_veri(db_session)

        urun = _olustur_urun(db_session, marka.id, kategori.id, "multi-test")
        lot = _olustur_lot(db_session, urun.id, "LOT-MULTI-001")
        db_session.commit()

        thread_sayisi = 5
        lot_id = lot.id
        raf_id = raf.id

        # Her thread kendi indeksini bilecek — closure ile
        sonuclar = [None] * thread_sayisi
        barrier = threading.Barrier(thread_sayisi)

        def worker_factory(idx):
            def worker_fn(session):
                # Barrier zaten _thread_worker tarafından çağrılıyor
                palet = PaletORM(
                    lot_id=lot_id,
                    raf_id=raf_id,
                    palet_no=f"PLT-MULTI-{idx:03d}",
                    koli_adedi=10,
                    aktif=True,
                )
                session.add(palet)
                session.commit()
                return palet.id
            return worker_fn

        threads = []
        for i in range(thread_sayisi):
            t = threading.Thread(
                target=_thread_worker,
                args=(engine, worker_factory(i), sonuclar, i, barrier),
            )
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        basarili = [s for s in sonuclar if s and s[0] == "basarili"]
        assert len(basarili) == thread_sayisi, (
            f"{thread_sayisi}/{thread_sayisi} başarılı olmalıydı, "
            f"oldu: {len(basarili)}. Hatalar: {[s for s in sonuclar if s and s[0] == 'hata']}"
        )

        # DB'de 5 ayrı palet olduğunu doğrula
        kontrol_session = _yeni_session(engine)
        try:
            sayac = kontrol_session.query(func.count(PaletORM.id)).filter(
                PaletORM.palet_no.like("PLT-MULTI-%")
            ).scalar()
            assert sayac == thread_sayisi
        finally:
            kontrol_session.close()



# ═══════════════════════════════════════════
# TEST SINIFI 2: FIFO Çıkış Yarışı
# ═══════════════════════════════════════════

class TestFifoCikisYarisi:
    """FIFO stok çıkışında SELECT FOR UPDATE kilit mekanizmasını doğrular."""

    def test_paralel_fifo_cikis_stok_yeterli(self, engine, db_session):
        """3 palet × 10 koli = 30 koli toplam stok.
        3 thread eşzamanlı 10'ar koli çıkış ister.
        Tümü başarılı olmalı, toplam stok 0'a düşmeli.
        """
        _temiz_basla(db_session)
        depo, raf, marka, kategori, kullanici = _seed_temel_veri(db_session)

        urun = _olustur_urun(db_session, marka.id, kategori.id, "fifo-yeterli")
        lot = _olustur_lot(db_session, urun.id, "LOT-FIFO-Y", skt=date(2027, 6, 1))
        for i in range(3):
            _olustur_palet(db_session, lot.id, raf.id, f"PLT-FIFO-Y-{i:03d}", koli_adedi=10)
        db_session.commit()

        urun_id = urun.id
        barrier = threading.Barrier(3)

        def worker_fn(session):
            """Bir thread: FIFO ile 10 koli düşür."""

            # SELECT FOR UPDATE ile paletleri kilitle
            paletler = (
                session.query(PaletORM)
                .join(LotORM)
                .filter(
                    LotORM.urun_id == urun_id,
                    LotORM.aktif == True,
                    PaletORM.aktif == True,
                    PaletORM.koli_adedi > 0,
                )
                .with_for_update()
                .all()
            )

            kalan = 10
            for palet in paletler:
                if kalan <= 0:
                    break
                dusulecek = min(kalan, palet.koli_adedi)
                palet.koli_adedi -= dusulecek
                if palet.koli_adedi == 0:
                    palet.aktif = False
                kalan -= dusulecek

            session.commit()
            return 10 - kalan  # düşürülen miktar

        sonuclar = _calistir_paralel(engine, worker_fn, 3, barrier)

        basarili = [s for s in sonuclar if s and s[0] == "basarili"]
        assert len(basarili) == 3, f"3/3 başarılı olmalıydı, oldu: {len(basarili)}"

        # Toplam düşürülen miktar doğrulama
        toplam_dusurulen = sum(s[1] for s in basarili)
        assert toplam_dusurulen == 30, f"Toplam 30 koli düşürülmeliydi, oldu: {toplam_dusurulen}"

        # DB'de stok negatife düşmemiş olmalı
        kontrol_session = _yeni_session(engine)
        try:
            paletler = kontrol_session.query(PaletORM).filter(
                PaletORM.palet_no.like("PLT-FIFO-Y-%")
            ).all()
            for p in paletler:
                assert p.koli_adedi >= 0, f"Palet {p.palet_no} negatife düşmüş: {p.koli_adedi}"
            toplam = sum(p.koli_adedi for p in paletler)
            assert toplam == 0, f"Toplam stok 0 olmalıydı, oldu: {toplam}"
        finally:
            kontrol_session.close()

    def test_paralel_fifo_cikis_stok_yetersiz(self, engine, db_session):
        """2 palet × 10 koli = 20 koli toplam.
        3 thread eşzamanlı 10'ar koli çıkış ister (toplam talep: 30).
        En fazla 2 başarılı, en az 1 hata almalı.
        """
        _temiz_basla(db_session)
        depo, raf, marka, kategori, kullanici = _seed_temel_veri(db_session)

        urun = _olustur_urun(db_session, marka.id, kategori.id, "fifo-yetersiz")
        lot = _olustur_lot(db_session, urun.id, "LOT-FIFO-N", skt=date(2027, 6, 1))
        for i in range(2):
            _olustur_palet(db_session, lot.id, raf.id, f"PLT-FIFO-N-{i:03d}", koli_adedi=10)
        db_session.commit()

        urun_id = urun.id
        barrier = threading.Barrier(3)

        def worker_fn(session):
            """Bir thread: FIFO ile 10 koli çıkış — yetersiz stok hata fırlatır."""

            paletler = (
                session.query(PaletORM)
                .join(LotORM)
                .filter(
                    LotORM.urun_id == urun_id,
                    LotORM.aktif == True,
                    PaletORM.aktif == True,
                    PaletORM.koli_adedi > 0,
                )
                .with_for_update()
                .all()
            )

            kalan = 10
            for palet in paletler:
                if kalan <= 0:
                    break
                dusulecek = min(kalan, palet.koli_adedi)
                palet.koli_adedi -= dusulecek
                if palet.koli_adedi == 0:
                    palet.aktif = False
                kalan -= dusulecek

            if kalan > 0:
                session.rollback()
                raise ValueError(f"Yetersiz stok: {kalan} koli eksik")

            session.commit()
            return 10

        sonuclar = _calistir_paralel(engine, worker_fn, 3, barrier)

        basarili = [s for s in sonuclar if s and s[0] == "basarili"]
        hatali = [s for s in sonuclar if s and s[0] == "hata"]

        assert len(basarili) <= 2, f"En fazla 2 başarılı olmalıydı, oldu: {len(basarili)}"
        assert len(hatali) >= 1, f"En az 1 hata olmalıydı, oldu: {len(hatali)}"

        # Toplam düşürülen ≤ 20
        toplam_dusurulen = sum(s[1] for s in basarili)
        assert toplam_dusurulen <= 20, f"Toplam düşürülen 20'yi aşmamalıydı: {toplam_dusurulen}"

        # DB'de stok negatife düşmemiş olmalı
        kontrol_session = _yeni_session(engine)
        try:
            paletler = kontrol_session.query(PaletORM).filter(
                PaletORM.palet_no.like("PLT-FIFO-N-%")
            ).all()
            for p in paletler:
                assert p.koli_adedi >= 0, f"Palet {p.palet_no} negatife düşmüş: {p.koli_adedi}"
        finally:
            kontrol_session.close()

    def test_fifo_sira_korunur_skt_bazli(self, engine, db_session):
        """3 palet farklı SKT ile — FIFO çıkışta en erken SKT'li önce tüketilmeli."""
        _temiz_basla(db_session)
        depo, raf, marka, kategori, kullanici = _seed_temel_veri(db_session)

        urun = _olustur_urun(db_session, marka.id, kategori.id, "fifo-sira")

        # SKT sırası: lot1 (2027-01) < lot2 (2027-06) < lot3 (2028-01)
        lot1 = _olustur_lot(db_session, urun.id, "LOT-SIRA-1", skt=date(2027, 1, 1))
        lot2 = _olustur_lot(db_session, urun.id, "LOT-SIRA-2", skt=date(2027, 6, 1))
        lot3 = _olustur_lot(db_session, urun.id, "LOT-SIRA-3", skt=date(2028, 1, 1))

        p1 = _olustur_palet(db_session, lot1.id, raf.id, "PLT-SIRA-1", koli_adedi=5)
        p2 = _olustur_palet(db_session, lot2.id, raf.id, "PLT-SIRA-2", koli_adedi=5)
        p3 = _olustur_palet(db_session, lot3.id, raf.id, "PLT-SIRA-3", koli_adedi=5)
        db_session.commit()

        urun_id = urun.id

        # 7 koli çıkış — FIFO: lot1'den 5, lot2'den 2
        test_session = _yeni_session(engine)
        try:
            from sqlalchemy import case as sa_case
            paletler = (
                test_session.query(PaletORM)
                .join(LotORM)
                .filter(
                    LotORM.urun_id == urun_id,
                    LotORM.aktif == True,
                    PaletORM.aktif == True,
                    PaletORM.koli_adedi > 0,
                )
                .order_by(
                    sa_case((LotORM.son_kullanma_tarihi.is_(None), 1), else_=0),
                    LotORM.son_kullanma_tarihi.asc(),
                    PaletORM.tarih.asc(),
                )
                .with_for_update()
                .all()
            )

            kalan = 7
            for palet in paletler:
                if kalan <= 0:
                    break
                dusulecek = min(kalan, palet.koli_adedi)
                palet.koli_adedi -= dusulecek
                if palet.koli_adedi == 0:
                    palet.aktif = False
                kalan -= dusulecek

            test_session.commit()
        finally:
            test_session.close()

        # Doğrulama
        kontrol = _yeni_session(engine)
        try:
            p1_db = kontrol.query(PaletORM).filter(PaletORM.palet_no == "PLT-SIRA-1").first()
            p2_db = kontrol.query(PaletORM).filter(PaletORM.palet_no == "PLT-SIRA-2").first()
            p3_db = kontrol.query(PaletORM).filter(PaletORM.palet_no == "PLT-SIRA-3").first()

            # SKT 2027-01: tamamen tüketilmiş (5 koli → 0)
            assert p1_db.koli_adedi == 0, f"PLT-SIRA-1 tamamen tüketilmeliydi: {p1_db.koli_adedi}"
            assert p1_db.aktif == False

            # SKT 2027-06: kısmen tüketilmiş (5 - 2 = 3)
            assert p2_db.koli_adedi == 3, f"PLT-SIRA-2 kısmen tüketilmeliydi: {p2_db.koli_adedi}"

            # SKT 2028-01: hiç tüketilmemiş
            assert p3_db.koli_adedi == 5, f"PLT-SIRA-3 dokunulmamalıydı: {p3_db.koli_adedi}"
        finally:
            kontrol.close()


# ═══════════════════════════════════════════
# TEST SINIFI 3: Palet Çıkış Eşzamanlılığı
# ═══════════════════════════════════════════

class TestPaletCikisEszamanlilik:
    """Aynı paletten eşzamanlı kısmi çıkış senaryosunu test eder."""

    def test_ayni_paletten_paralel_kismi_cikis(self, engine, db_session):
        """1 palet, 20 koli. 4 thread eşzamanlı 5'er koli kısmi çıkış ister.
        SELECT FOR UPDATE ile sıralı erişim → toplam 20 koli düşmeli.
        """
        _temiz_basla(db_session)
        depo, raf, marka, kategori, kullanici = _seed_temel_veri(db_session)

        urun = _olustur_urun(db_session, marka.id, kategori.id, "kismi-cikis")
        lot = _olustur_lot(db_session, urun.id, "LOT-KISMI-001")
        palet = _olustur_palet(db_session, lot.id, raf.id, "PLT-KISMI-001", koli_adedi=20)
        db_session.commit()

        palet_id = palet.id
        barrier = threading.Barrier(4)

        def worker_fn(session):
            """5 koli kısmi çıkış: SELECT FOR UPDATE ile kilit al, düşür, commit."""

            palet_orm = (
                session.query(PaletORM)
                .filter(PaletORM.id == palet_id)
                .with_for_update()
                .first()
            )

            if not palet_orm or palet_orm.koli_adedi < 5:
                session.rollback()
                raise ValueError(
                    f"Yetersiz stok: mevcut={palet_orm.koli_adedi if palet_orm else 0}"
                )

            palet_orm.koli_adedi -= 5
            if palet_orm.koli_adedi == 0:
                palet_orm.aktif = False
            session.commit()
            return 5

        sonuclar = _calistir_paralel(engine, worker_fn, 4, barrier)

        basarili = [s for s in sonuclar if s and s[0] == "basarili"]
        toplam_dusurulen = sum(s[1] for s in basarili)

        assert len(basarili) == 4, (
            f"4/4 başarılı olmalıydı, oldu: {len(basarili)}. "
            f"Hatalar: {[s for s in sonuclar if s and s[0] == 'hata']}"
        )
        assert toplam_dusurulen == 20, f"Toplam 20 koli düşürülmeliydi, oldu: {toplam_dusurulen}"

        # DB doğrulaması
        kontrol = _yeni_session(engine)
        try:
            p = kontrol.query(PaletORM).filter(PaletORM.id == palet_id).first()
            assert p.koli_adedi == 0, f"Palet koli_adedi 0 olmalıydı: {p.koli_adedi}"
            assert p.aktif == False, "Palet artık aktif olmamalıydı"
        finally:
            kontrol.close()


# ═══════════════════════════════════════════
# TEST SINIFI 4: Deadlock Dayanıklılığı
# ═══════════════════════════════════════════

class TestDeadlockDayanakliligi:
    """MySQL InnoDB deadlock detection altında stok tutarsızlığı oluşmadığını doğrular."""

    def test_capraz_palet_erisimi_deadlock_dayanikliligi(self, engine, db_session):
        """2 palet (P1, P2): Thread A → P1 sonra P2, Thread B → P2 sonra P1.
        Deadlock olabilir — MySQL otomatik algılar ve 1 transaction'ı rollback eder.
        Stok negatife düşmemeli, veri tutarlılığı korunmalı.
        """
        _temiz_basla(db_session)
        depo, raf, marka, kategori, kullanici = _seed_temel_veri(db_session)

        urun = _olustur_urun(db_session, marka.id, kategori.id, "deadlock-test")
        lot = _olustur_lot(db_session, urun.id, "LOT-DEADLOCK")
        p1 = _olustur_palet(db_session, lot.id, raf.id, "PLT-DL-001", koli_adedi=10)
        p2 = _olustur_palet(db_session, lot.id, raf.id, "PLT-DL-002", koli_adedi=10)
        db_session.commit()

        p1_id, p2_id = p1.id, p2.id
        barrier = threading.Barrier(2)
        sonuclar = [None, None]

        def worker_a(session):
            """Thread A: P1'i kilitle → kısa bekleme → P2'yi kilitle → düşür → commit."""
            barrier.wait(timeout=10)
            pa1 = session.query(PaletORM).filter(PaletORM.id == p1_id).with_for_update().first()
            pa1.koli_adedi -= 2
            time.sleep(0.3)  # P2 kilidini thread B'nin almasını sağla
            pa2 = session.query(PaletORM).filter(PaletORM.id == p2_id).with_for_update().first()
            pa2.koli_adedi -= 2
            session.commit()
            return "A tamamlandi"

        def worker_b(session):
            """Thread B: P2'yi kilitle → kısa bekleme → P1'i kilitle → düşür → commit."""
            barrier.wait(timeout=10)
            pb2 = session.query(PaletORM).filter(PaletORM.id == p2_id).with_for_update().first()
            pb2.koli_adedi -= 2
            time.sleep(0.3)  # P1 kilidini thread A'nın almasını sağla
            pb1 = session.query(PaletORM).filter(PaletORM.id == p1_id).with_for_update().first()
            pb1.koli_adedi -= 2
            session.commit()
            return "B tamamlandi"

        def run_worker(fn, idx):
            session = _yeni_session(engine)
            try:
                result = fn(session)
                sonuclar[idx] = ("basarili", result)
            except Exception as e:
                session.rollback()
                sonuclar[idx] = ("hata", f"{type(e).__name__}: {e}")
            finally:
                session.close()

        t_a = threading.Thread(target=run_worker, args=(worker_a, 0))
        t_b = threading.Thread(target=run_worker, args=(worker_b, 1))

        t_a.start()
        t_b.start()
        t_a.join(timeout=30)
        t_b.join(timeout=30)

        basarili = [s for s in sonuclar if s and s[0] == "basarili"]
        hatali = [s for s in sonuclar if s and s[0] == "hata"]

        # Deadlock: MySQL en az 1 tarafı rollback eder
        # Veya kilit sırası şanslıysa ikisi de başarılı olabilir
        # Önemli olan: stok negatife düşmemeli
        assert len(basarili) >= 1, (
            f"En az 1 thread başarılı olmalıydı. Sonuçlar: {sonuclar}"
        )

        # ** KRİTİK DOĞRULAMA **: Stok negatife düşmemiş olmalı
        kontrol = _yeni_session(engine)
        try:
            pa1 = kontrol.query(PaletORM).filter(PaletORM.id == p1_id).first()
            pa2 = kontrol.query(PaletORM).filter(PaletORM.id == p2_id).first()

            assert pa1.koli_adedi >= 0, f"P1 negatife düşmüş: {pa1.koli_adedi}"
            assert pa2.koli_adedi >= 0, f"P2 negatife düşmüş: {pa2.koli_adedi}"

            # Tutarlılık: başarılı thread sayısına göre stok düşmüş olmalı
            basarili_count = len(basarili)
            if basarili_count == 2:
                # İki thread de başarılı → her paletten 2+2 = 4 düşmüş
                assert pa1.koli_adedi == 6, f"P1: 10-4=6 olmalıydı: {pa1.koli_adedi}"
                assert pa2.koli_adedi == 6, f"P2: 10-4=6 olmalıydı: {pa2.koli_adedi}"
            elif basarili_count == 1:
                # Sadece 1 thread başarılı → her paletten 2 düşmüş
                assert pa1.koli_adedi == 8, f"P1: 10-2=8 olmalıydı: {pa1.koli_adedi}"
                assert pa2.koli_adedi == 8, f"P2: 10-2=8 olmalıydı: {pa2.koli_adedi}"
        finally:
            kontrol.close()
