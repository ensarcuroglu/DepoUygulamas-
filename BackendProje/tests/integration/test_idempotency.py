"""
Faz 2 — Idempotency Testleri (Test 4.3)

API endpoint'leri üzerinden idempotency davranışını doğrular:
- Aynı Idempotency-Key ile iki kez POST → ikinci istek cache'den döner
- DB'de işlem yalnızca bir kez gerçekleşir
- Farklı key → yeni işlem tetiklenir

Test edilen endpoint'ler: /api/v1/toplama-gorevleri/sira-al
"""

import uuid

import pytest

from models import (
    ToplamaGorevi as ToplamaGoreviORM,
    IdempotencyKaydi,
)
from sqlalchemy import func

pytestmark = pytest.mark.integration


# ═══════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════

def _gorev_olustur(db_session, sira_no=1):
    """Test için ön koşul verisi: bir Beklemede toplama görevi oluşturur."""
    from tests.factories import (
        PaletFactory, LotFactory, UrunFactory,
        DepoFactory, SevkiyatPlaniFactory, SiparisFactory,
    )

    depo = DepoFactory.create()
    urun = UrunFactory.create()
    lot = LotFactory.create(urun=urun)
    palet = PaletFactory.create(lot=lot)
    siparis = SiparisFactory.create(durum="Hazirlanıyor")
    sevkiyat = SevkiyatPlaniFactory.create(siparis=siparis)

    gorev = ToplamaGoreviORM(
        sevkiyat_id=sevkiyat.id,
        palet_id=palet.id,
        lot_id=lot.id,
        urun_id=urun.id,
        depo_id=depo.id,
        durum="Beklemede",
        sira_no=sira_no,
    )
    db_session.add(gorev)
    db_session.commit()
    return gorev, depo


# ═══════════════════════════════════════════
# TEST SINIFI: Sira-Al Idempotency
# ═══════════════════════════════════════════

class TestSiradanGorevAlIdempotency:
    """
    /sira-al endpoint'ine aynı Idempotency-Key ile iki kez istek gönderildiğinde:
    - İkinci istek cache'den döner (görev tekrar atanmaz)
    - DB'deki idempotency_kayitlari tablosunda kayıt oluşur
    """

    def test_ayni_key_ile_iki_istek_ayni_yaniti_doner(self, admin_client, db_session):
        """Aynı Idempotency-Key ile /sira-al iki kez çağrılır; ikinci istek cache'den döner."""
        gorev, depo = _gorev_olustur(db_session)
        key = f"test-sirada-{uuid.uuid4().hex}"

        payload = {"depo_id": depo.id}
        headers = {"Idempotency-Key": key}

        # İlk istek — gerçek işlem
        r1 = admin_client.post(
            "/api/v1/toplama-gorevleri/sira-al",
            json=payload,
            headers=headers,
        )
        assert r1.status_code == 200, f"İlk istek başarısız: {r1.text}"
        data1 = r1.json()
        assert data1 is not None, "İlk istek bir görev döndürmelidir"
        assert data1["id"] == gorev.id

        # İkinci istek — aynı key, cache'den dönmeli
        r2 = admin_client.post(
            "/api/v1/toplama-gorevleri/sira-al",
            json=payload,
            headers=headers,
        )
        assert r2.status_code == 200, f"İkinci istek başarısız: {r2.text}"
        data2 = r2.json()
        assert data2 is not None
        assert data2["id"] == data1["id"], (
            f"Cache'den dönen yanıt farklı: beklenen {data1['id']}, gelen {data2['id']}"
        )
        assert data2["durum"] == data1["durum"], "Cache yanıtı orijinal ile aynı durum içermeli"

        # DB: idempotency kaydı oluşmuş olmalı
        kayit = db_session.query(IdempotencyKaydi).filter(
            IdempotencyKaydi.idempotency_key == key,
            IdempotencyKaydi.endpoint == "siradan_gorev_al",
        ).first()
        assert kayit is not None, "Idempotency kaydı DB'de oluşturulmalıdır"
        kayit_sayisi = db_session.query(func.count(IdempotencyKaydi.idempotency_key)).filter(
            IdempotencyKaydi.idempotency_key == key,
            IdempotencyKaydi.endpoint == "siradan_gorev_al",
        ).scalar()
        assert kayit_sayisi == 1, "Aynı key için yalnızca tek idempotency kaydı olmalıdır"

    def test_farkli_key_ile_yeni_islem_tetiklenir(self, admin_client, db_session):
        """Farklı Idempotency-Key ile ikinci çağrı yeni işlemi tetikler."""
        gorev1, depo = _gorev_olustur(db_session, sira_no=1)
        gorev2, _ = _gorev_olustur(db_session, sira_no=2)

        payload = {"depo_id": depo.id}
        key1 = f"test-key-{uuid.uuid4().hex}"
        key2 = f"test-key-{uuid.uuid4().hex}"

        r1 = admin_client.post(
            "/api/v1/toplama-gorevleri/sira-al",
            json=payload,
            headers={"Idempotency-Key": key1},
        )
        assert r1.status_code == 200
        data1 = r1.json()

        r2 = admin_client.post(
            "/api/v1/toplama-gorevleri/sira-al",
            json=payload,
            headers={"Idempotency-Key": key2},
        )
        assert r2.status_code == 200
        data2 = r2.json()

        # Farklı key → farklı görev (görev1 AtanmaBekliyor, görev2 alınabilir)
        if data2 is not None and data1 is not None:
            assert data1["id"] != data2["id"], (
                "Farklı key'lerle farklı görevler atanmalıydı"
            )

    def test_key_olmadan_tekrar_istek_tekrar_islem_yapar(self, admin_client, db_session):
        """Idempotency-Key olmadan /sira-al her çağrıda yeni işlemi tetikler."""
        gorev1, depo = _gorev_olustur(db_session, sira_no=1)
        gorev2, _ = _gorev_olustur(db_session, sira_no=2)

        payload = {"depo_id": depo.id}

        r1 = admin_client.post("/api/v1/toplama-gorevleri/sira-al", json=payload)
        assert r1.status_code == 200

        r2 = admin_client.post("/api/v1/toplama-gorevleri/sira-al", json=payload)
        assert r2.status_code == 200

        d1 = r1.json()
        d2 = r2.json()

        # Farklı görevler alınmalı (key olmadan idempotency yok)
        if d1 and d2:
            assert d1["id"] != d2["id"], "Key olmadan her istek yeni görevi almalıdır"


# ═══════════════════════════════════════════
# TEST SINIFI: GorevUret Idempotency
# ═══════════════════════════════════════════

class TestGorevUretIdempotency:
    """
    /uret endpoint'ine aynı Idempotency-Key ile iki kez istek gönderildiğinde
    görevler yalnızca bir kez üretilir.
    """

    def _setup_sevkiyat_ile_rezervasyon(self, db_session):
        """SevkiyatPlani + aktif PaletRezervasyonu + gerekli veri oluşturur."""
        from tests.factories import (
            PaletFactory, LotFactory, UrunFactory,
            SevkiyatPlaniFactory, SiparisFactory, SiparisKalemiFactory,
        )
        from models import PaletRezervasyonu as PaletRezervasyonuORM

        urun = UrunFactory.create()
        lot = LotFactory.create(urun=urun)
        palet = PaletFactory.create(lot=lot)
        siparis = SiparisFactory.create(durum="Hazirlanıyor")
        kalem = SiparisKalemiFactory.create(siparis=siparis, urun=urun, miktar=5)
        sevkiyat = SevkiyatPlaniFactory.create(siparis=siparis)

        # Aktif rezervasyon (PickTaskUretUseCase için zorunlu)
        rezervasyon = PaletRezervasyonuORM(
            palet_id=palet.id,
            siparis_id=siparis.id,
            durum="Aktif",
        )
        db_session.add(rezervasyon)
        db_session.commit()

        return sevkiyat

    def test_ayni_key_ile_iki_uret_istegi_ayni_gorevi_doner(self, admin_client, db_session):
        """Aynı Idempotency-Key ile /uret iki kez çağrılır; görevler yalnızca bir kez üretilir."""
        sevkiyat = self._setup_sevkiyat_ile_rezervasyon(db_session)
        key = f"test-uret-{uuid.uuid4().hex}"

        payload = {"sevkiyat_id": sevkiyat.id}
        headers = {"Idempotency-Key": key}

        r1 = admin_client.post(
            "/api/v1/toplama-gorevleri/uret",
            json=payload,
            headers=headers,
        )
        assert r1.status_code == 201, f"İlk istek başarısız: {r1.text}"
        gorevler1 = r1.json()
        assert isinstance(gorevler1, list)
        assert len(gorevler1) >= 1

        # İkinci istek — cache'den dönmeli, yeni görev üretilmemeli
        r2 = admin_client.post(
            "/api/v1/toplama-gorevleri/uret",
            json=payload,
            headers=headers,
        )
        assert r2.status_code == 200, f"İkinci istek cache hit olarak 200 dönmeliydi: {r2.text}"
        gorevler2 = r2.json()

        assert len(gorevler2) == len(gorevler1), "Cache'deki ve gerçek yanıt aynı uzunlukta olmalı"
        ids1 = {g["id"] for g in gorevler1}
        ids2 = {g["id"] for g in gorevler2}
        assert ids1 == ids2, f"Cache'den dönen görevler farklı: {ids1} vs {ids2}"

        # DB: toplama_gorevleri tablosunda sevkiyat için yalnızca 1 set görev var
        db_gorev_sayisi = db_session.query(func.count(ToplamaGoreviORM.id)).filter(
            ToplamaGoreviORM.sevkiyat_id == sevkiyat.id
        ).scalar()
        assert db_gorev_sayisi == len(gorevler1), (
            f"DB'de {db_gorev_sayisi} görev var, {len(gorevler1)} olmalıydı (çift üretim engellenmeli)"
        )
        kayit_sayisi = db_session.query(func.count(IdempotencyKaydi.idempotency_key)).filter(
            IdempotencyKaydi.idempotency_key == key,
            IdempotencyKaydi.endpoint == "gorev_uret",
        ).scalar()
        assert kayit_sayisi == 1, "Aynı key için yalnızca tek idempotency kaydı olmalıdır"
