"""
Faz 2 — Refresh Token Rotation & Replay Detection Testleri (Test 4.4)

Doğrulanan davranışlar:
- /refresh çağrısı yeni access_token + refresh_token döner (rotation)
- Eski refresh_token artık geçersizdir (rotation sonrası replay engeli)
- Çalınmış eski token ile /refresh → 401 + oturum kapatılır
- Yeni refresh_token ile tekrar /refresh → başarılı

Test tipi: Entegrasyon (TestClient + DB)
"""

import pytest
from datetime import datetime, timedelta, timezone

from models import Kullanici
from tests.conftest import TEST_PASSWORD
from tests.factories import KullaniciFactory  # Factory'yi en üste aldık

pytestmark = pytest.mark.integration


# ═══════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════

def _login(client, kullanici_adi: str, sifre: str) -> dict:
    """Giriş endpoint'ini çağırır, token yanıtını döner."""
    r = client.post(
        "/api/auth/login",
        json={"kullanici_adi": kullanici_adi, "sifre": sifre},
    )
    assert r.status_code == 200, f"Login başarısız: {r.text}"
    return r.json()


def _refresh(client, refresh_token: str) -> tuple[int, dict | None]:
    """Refresh endpoint'ini çağırır, (status_code, body) döner."""
    r = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    body = r.json() if r.headers.get("content-type", "").startswith("application/json") else None
    return r.status_code, body


# ═══════════════════════════════════════════
# TEST SINIFI: Token Rotation
# ═══════════════════════════════════════════

class TestTokenRotation:
    """
    Her başarılı /refresh çağrısı yeni token çifti döndürür;
    eski refresh_token geçersizleştirilir.
    """

    @pytest.fixture(autouse=True)
    def setup_factories(self, db_session):
        """
        Bu sınıftaki HER testten önce otomatik çalışır.
        KullaniciFactory'nin ihtiyaç duyduğu db_session'ı bağlar.
        """
        KullaniciFactory._meta.sqlalchemy_session = db_session

    def test_refresh_yeni_token_donduruyor(self, client, db_session):
        """Başarılı /refresh → yeni access_token ve refresh_token döner."""
        user = KullaniciFactory.create(kullanici_adi="rot_test_basic", rol="depocu")

        data = _login(client, user.kullanici_adi, TEST_PASSWORD)
        eski_access = data["access_token"]
        eski_refresh = data["refresh_token"]

        status, body = _refresh(client, eski_refresh)

        assert status == 200, f"/refresh başarısız: {body}"
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

        # Yeni token'lar eskilerinden farklı olmalı
        assert body["access_token"] != eski_access, "Access token rotation'da değişmelidir"
        assert body["refresh_token"] != eski_refresh, "Refresh token rotation'da değişmelidir"

    def test_eski_refresh_token_gecersizlesiyor(self, client, db_session):
        """
        Rotation sonrası eski refresh_token artık çalışmaz.
        Replay saldırısı simülasyonu: eski token tekrar gönderilir → 401.
        """
        user = KullaniciFactory.create(kullanici_adi="rot_test_replay", rol="depocu")

        data = _login(client, user.kullanici_adi, TEST_PASSWORD)
        eski_refresh = data["refresh_token"]

        # İlk rotation: başarılı
        status1, body1 = _refresh(client, eski_refresh)
        assert status1 == 200, f"İlk rotation başarısız: {body1}"

        # Eski token ile tekrar deneme → 401 (replay detection)
        status2, body2 = _refresh(client, eski_refresh)
        assert status2 == 401, (
            f"Eski (rotated) token ile /refresh 401 dönmelidir, dönen: {status2}. Body: {body2}"
        )

    def test_replay_tespiti_oturumu_kapatir(self, client, db_session):
        """
        Replay saldırısı tespit edildiğinde kullanıcının tüm oturumu sonlandırılır.
        Sonraki yeni bir refresh_token girişimi de 401 döner.
        """
        user = KullaniciFactory.create(kullanici_adi="rot_test_terminate", rol="depocu")

        data = _login(client, user.kullanici_adi, TEST_PASSWORD)
        eski_refresh = data["refresh_token"]

        # Rotation: yeni token alındı
        status1, body1 = _refresh(client, eski_refresh)
        assert status1 == 200
        yeni_refresh = body1["refresh_token"]

        # Replay: eski token tekrar kullanılır → replay tespiti → session sonlandırma
        status_replay, _ = _refresh(client, eski_refresh)
        assert status_replay == 401, "Replay tespitinde 401 bekleniyor"

        # Session sonlandı: yeni token da artık çalışmıyor
        status_yeni, _ = _refresh(client, yeni_refresh)
        assert status_yeni == 401, (
            "Session sonlandırıldıktan sonra yeni token da geçersiz olmalıdır"
        )

        # DB: kullanıcının refresh_token_hash'i NULL olmalı
        db_session.expire_all()
        db_kullanici = db_session.query(Kullanici).filter(
            Kullanici.kullanici_adi == user.kullanici_adi
        ).first()
        assert db_kullanici.refresh_token_hash is None, (
            "Session sonlandırıldıktan sonra refresh_token_hash NULL olmalıdır"
        )

    def test_yeni_token_ile_tekrar_refresh_edilebiliyor(self, client, db_session):
        """Rotation sonrası yeni refresh_token tekrar kullanılabilir."""
        user = KullaniciFactory.create(kullanici_adi="rot_test_chain", rol="depocu")

        data = _login(client, user.kullanici_adi, TEST_PASSWORD)
        refresh1 = data["refresh_token"]

        # İlk rotation
        status1, body1 = _refresh(client, refresh1)
        assert status1 == 200
        refresh2 = body1["refresh_token"]

        # İkinci rotation — yeni token ile
        status2, body2 = _refresh(client, refresh2)
        assert status2 == 200, f"İkinci rotation başarısız: {body2}"
        assert "access_token" in body2
        assert "refresh_token" in body2

    def test_gecersiz_format_401_doner(self, client, db_session):
        """Hatalı formatta refresh_token → 401."""
        status, body = _refresh(client, "gecersiz_format_token")
        assert status == 401, f"Hatalı format 401 dönmelidir, dönen: {status}"

    def test_suresi_dolmus_token_401_doner(self, client, db_session):
        """
        Süresi dolmuş refresh_token → 401.
        refresh_token_son_kullanim geçmişe set edilerek simüle edilir.
        """
        from app.core.auth import create_refresh_token, hash_token

        user = KullaniciFactory.create(kullanici_adi="rot_test_expired", rol="depocu")

        # Süresi geçmiş token simülasyonu
        raw_refresh = create_refresh_token(user.id)
        _, raw_part = raw_refresh.split(":", 1)

        db_kullanici = db_session.query(Kullanici).filter(
            Kullanici.id == user.id
        ).first()
        db_kullanici.refresh_token_hash = hash_token(raw_part)
        
        # ÇÖZÜM: DeprecationWarning almamak için utcnow() yerine now(timezone.utc) kullandık
        db_kullanici.refresh_token_son_kullanim = datetime.now(timezone.utc) - timedelta(days=1)
        db_session.commit()

        status, body = _refresh(client, raw_refresh)
        assert status == 401, f"Süresi dolmuş token 401 dönmelidir, dönen: {status}"

    def test_logout_sonrasi_refresh_401_doner(self, client, db_session):
        """Logout yapıldıktan sonra refresh_token artık çalışmaz."""
        user = KullaniciFactory.create(kullanici_adi="rot_test_logout", rol="depocu")

        data = _login(client, user.kullanici_adi, TEST_PASSWORD)
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]

        # Logout
        r_logout = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert r_logout.status_code == 200

        # Logout sonrası refresh denemesi → 401
        status, body = _refresh(client, refresh_token)
        assert status == 401, (
            f"Logout sonrası refresh 401 dönmelidir, dönen: {status}. Body: {body}"
        )