"""API testleri — Üretim Paleti feature flag (pilot depo kontrolü).

lru_cache'li get_feature_flags arasında izolasyon sağlamak için
her test fixture'ı cache'i temizler.
"""

import pytest
from datetime import date
from tests.factories import (
    KullaniciFactory,
    DepoFactory,
    RafFactory,
    LotFactory,
    PaletFactory,
)
from app.core.auth import create_access_token
from app.core.entities.palet import UretimPaletDurum

pytestmark = pytest.mark.api

PRD_NO = "PRD-FF-TEST-0001"


# ─────────────────────────────────────────────────────────────────────────────
# Cache yönetimi
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _temizle_flag_cache():
    """Her test öncesi ve sonrası feature flag cache'ini temizler."""
    from app.core.config import get_feature_flags
    get_feature_flags.cache_clear()
    yield
    get_feature_flags.cache_clear()


@pytest.fixture
def pilot_kapali(monkeypatch):
    """Feature flag tamamen kapalı."""
    from app.core.config import get_feature_flags
    monkeypatch.setenv("FEATURE_URETIM_PALET_PILOT_DEPO_IDS", "")
    get_feature_flags.cache_clear()


@pytest.fixture
def pilot_tumu(monkeypatch):
    """Feature flag tüm depolar için açık (TUMU sentinel)."""
    from app.core.config import get_feature_flags
    monkeypatch.setenv("FEATURE_URETIM_PALET_PILOT_DEPO_IDS", "TUMU")
    get_feature_flags.cache_clear()


def _pilot_belirli_depo(monkeypatch, depo_id: int):
    from app.core.config import get_feature_flags
    monkeypatch.setenv("FEATURE_URETIM_PALET_PILOT_DEPO_IDS", str(depo_id))
    get_feature_flags.cache_clear()


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def pilot_depo_depocu(db_session):
    """Pilot depoya atanmış depocu kullanıcısı — depo_id=10 (mock)."""
    depo = DepoFactory.create()
    RafFactory.create(depo=depo, is_staging=True)
    user = KullaniciFactory.create(
        kullanici_adi="pilot_depocu",
        rol="depocu",
        depo_id=depo.id,
    )
    token = create_access_token(data={"sub": user.kullanici_adi})
    return user, token, depo


@pytest.fixture
def pilot_disinda_depocu(db_session):
    """Pilot dışı depoya atanmış depocu kullanıcısı."""
    depo = DepoFactory.create()
    user = KullaniciFactory.create(
        kullanici_adi="disinda_depocu",
        rol="depocu",
        depo_id=depo.id,
    )
    token = create_access_token(data={"sub": user.kullanici_adi})
    return user, token, depo


@pytest.fixture
def palet_mevcut(db_session):
    depo = DepoFactory.create()
    raf = RafFactory.create(depo=depo)
    lot = LotFactory.create()
    return PaletFactory.create(
        palet_no=PRD_NO,
        lot=lot,
        raf=raf,
        kaynak="uretim",
        durum=UretimPaletDurum.OLUSTURULDU,
        aktif=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Pilot dışı → 403
# ─────────────────────────────────────────────────────────────────────────────

class TestPilotDisinda403:
    def test_pilot_kapali_depocu_olusturamaz(
        self, client, pilot_kapali, pilot_disinda_depocu, db_session
    ):
        """Feature flag tamamen kapalıyken depocu olustur → 403 OZELLIK_PILOTA_KAPALI."""
        user, token, depo = pilot_disinda_depocu
        client.headers["Authorization"] = f"Bearer {token}"
        lot = LotFactory.create()

        r = client.post("/api/uretim-paletleri/", json={
            "lot_id": lot.id,
            "koli_adedi": 10,
            "depo_id": depo.id,
        })

        assert r.status_code == 403
        assert r.json()["detail"]["code"] == "OZELLIK_PILOTA_KAPALI"

    def test_pilot_kapali_depocu_kabul_edemez(
        self, client, pilot_kapali, pilot_disinda_depocu, palet_mevcut
    ):
        """Feature flag kapalıyken kabul-bekle → 403."""
        user, token, _ = pilot_disinda_depocu
        client.headers["Authorization"] = f"Bearer {token}"

        r = client.post(f"/api/uretim-paletleri/{PRD_NO}/kabul-bekle")
        assert r.status_code == 403

    def test_pilot_kapali_iptal_depocu_403(
        self, client, pilot_kapali, pilot_disinda_depocu, palet_mevcut
    ):
        user, token, _ = pilot_disinda_depocu
        client.headers["Authorization"] = f"Bearer {token}"

        r = client.post(
            f"/api/uretim-paletleri/{PRD_NO}/iptal",
            json={"palet_no": PRD_NO, "sebep": "Test"},
        )
        assert r.status_code == 403

    def test_belirli_pilot_depo_disindaki_depocu_403(
        self, client, monkeypatch, pilot_disinda_depocu, palet_mevcut
    ):
        """Pilot listesinde olmayan depo → 403."""
        user, token, depo = pilot_disinda_depocu
        _pilot_belirli_depo(monkeypatch, depo.id + 9999)  # Farklı depo ID
        client.headers["Authorization"] = f"Bearer {token}"

        r = client.post(f"/api/uretim-paletleri/{PRD_NO}/kabul-bekle")
        assert r.status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# Admin bypass — feature flag'den muaf
# ─────────────────────────────────────────────────────────────────────────────

class TestAdminBypass:
    def test_admin_pilot_kapali_olsa_da_erisebilir(
        self, admin_client, pilot_kapali, palet_mevcut
    ):
        """Admin rol → feature flag'den bağımsız, her zaman 200/işlem başarılı."""
        # GET (listele) — her zaman açık
        r = admin_client.get("/api/uretim-paletleri/")
        assert r.status_code == 200

    def test_admin_kabul_bekle_pilot_kapali(
        self, admin_client, pilot_kapali, palet_mevcut
    ):
        """Admin kabul-bekle işlemi feature flag kapalıyken çalışmalı."""
        r = admin_client.post(f"/api/uretim-paletleri/{PRD_NO}/kabul-bekle")
        assert r.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# Pilot içi depocu → 200
# ─────────────────────────────────────────────────────────────────────────────

class TestPilotIcinde200:
    def test_tumu_sentinel_depocu_200(
        self, client, pilot_tumu, pilot_depo_depocu, db_session
    ):
        """TUMU sentinel → tüm depocular erişebilir."""
        user, token, depo = pilot_depo_depocu
        client.headers["Authorization"] = f"Bearer {token}"
        lot = LotFactory.create()

        r = client.post("/api/uretim-paletleri/", json={
            "lot_id": lot.id,
            "koli_adedi": 10,
            "depo_id": depo.id,
        })

        assert r.status_code == 201

    def test_belirli_pilot_depo_icindeki_depocu_200(
        self, client, monkeypatch, pilot_depo_depocu, db_session
    ):
        """Pilot listesindeki depo ID → 200."""
        user, token, depo = pilot_depo_depocu
        _pilot_belirli_depo(monkeypatch, depo.id)
        client.headers["Authorization"] = f"Bearer {token}"
        lot = LotFactory.create()

        r = client.post("/api/uretim-paletleri/", json={
            "lot_id": lot.id,
            "koli_adedi": 10,
            "depo_id": depo.id,
        })

        assert r.status_code == 201

    def test_listele_ve_getir_herkese_acik_flag_bagimli_degil(
        self, client, pilot_kapali, db_session
    ):
        """GET listele/getir endpoint'leri feature flag dışında, tokeni olan herkes erişebilir."""
        from tests.factories import KullaniciFactory
        user = KullaniciFactory.create(kullanici_adi="ff_goruntuleyen", rol="goruntuleyen")
        token = create_access_token(data={"sub": user.kullanici_adi})
        client.headers["Authorization"] = f"Bearer {token}"

        r = client.get("/api/uretim-paletleri/")
        assert r.status_code == 200
