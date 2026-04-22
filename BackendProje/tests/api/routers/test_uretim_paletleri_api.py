"""API testleri — Üretim Paletleri endpoint'leri.

Yetki matrisi:
  listele / getir / etiket : tüm authenticated (admin, depocu, goruntuleyen)
  olustur                  : admin, depocu (staging raf gerekli)
  kabul-bekle / kabul-et   : admin, depocu
  karantina                : admin, depocu, kalite departmanı
  karantina-cikar          : admin, kalite departmanı; depocu → 403
  iptal                    : admin only
  yerlestirme-bekle        : admin, depocu
  yerlestir                : admin, depocu
"""

import pytest
from datetime import date
from tests.factories import (
    KullaniciFactory,
    DepoFactory,
    RafFactory,
    LotFactory,
    PaletFactory,
    UrunFactory,
)
from app.core.auth import create_access_token
from app.core.entities.palet import UretimPaletDurum

pytestmark = pytest.mark.api

PRD_NO = "PRD-20250416-0001"


# ─────────────────────────────────────────────────────────────────────────────
# Feature flag izolasyonu
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _uretim_paleti_flag_tumu(monkeypatch):
    """Genel API davranışı bu dosyada flag açıkken test edilir."""
    from app.core.config import get_feature_flags
    monkeypatch.setenv("FEATURE_URETIM_PALET_PILOT_DEPO_IDS", "TUMU")
    get_feature_flags.cache_clear()
    yield
    get_feature_flags.cache_clear()


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def goruntuleyen_user(db_session):
    user = KullaniciFactory.create(
        kullanici_adi="test_goruntuleyen",
        rol="goruntuleyen",
    )
    token = create_access_token(data={"sub": user.kullanici_adi})
    return user, token


@pytest.fixture
def goruntuleyen_client(client, goruntuleyen_user):
    _, token = goruntuleyen_user
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
def kalite_client(client, db_session):
    """Kalite departmanı goruntuleyen kullanıcısı — karantina işlemlerine yetkili."""
    user = KullaniciFactory.create(
        kullanici_adi="test_kalite",
        rol="goruntuleyen",
        departman="Kalite",
    )
    token = create_access_token(data={"sub": user.kullanici_adi})
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
def staging_raf(db_session, depocu_user):
    """depocu kullanıcısının deposundaki staging rafı."""
    depocu, _ = depocu_user
    return RafFactory.create(depo=depocu.depo, is_staging=True)


@pytest.fixture
def uretim_paleti_olusturuldu(db_session, staging_raf):
    """OLUSTURULDU durumunda üretim paleti."""
    lot = LotFactory.create()
    return PaletFactory.create(
        palet_no=PRD_NO,
        lot=lot,
        raf=staging_raf,
        kaynak="uretim",
        durum=UretimPaletDurum.OLUSTURULDU,
        aktif=True,
    )


@pytest.fixture
def uretim_paleti_kabul_bekliyor(db_session, staging_raf):
    lot = LotFactory.create()
    return PaletFactory.create(
        palet_no=PRD_NO,
        lot=lot,
        raf=staging_raf,
        kaynak="uretim",
        durum=UretimPaletDurum.KABUL_BEKLIYOR,
        aktif=True,
    )


@pytest.fixture
def uretim_paleti_kabul_edildi(db_session, staging_raf):
    lot = LotFactory.create()
    return PaletFactory.create(
        palet_no=PRD_NO,
        lot=lot,
        raf=staging_raf,
        kaynak="uretim",
        durum=UretimPaletDurum.KABUL_EDILDI,
        aktif=True,
    )


@pytest.fixture
def uretim_paleti_karantina(db_session, staging_raf):
    lot = LotFactory.create()
    return PaletFactory.create(
        palet_no=PRD_NO,
        lot=lot,
        raf=staging_raf,
        kaynak="uretim",
        durum=UretimPaletDurum.KARANTINA,
        aktif=True,
    )


@pytest.fixture
def uretim_paleti_yerlestirme_bekliyor(db_session, staging_raf):
    lot = LotFactory.create()
    return PaletFactory.create(
        palet_no=PRD_NO,
        lot=lot,
        raf=staging_raf,
        kaynak="uretim",
        durum=UretimPaletDurum.YERLESTIRME_BEKLIYOR,
        aktif=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/uretim-paletleri/  — listele
# ─────────────────────────────────────────────────────────────────────────────

class TestUretimPaletleriListele:
    def test_admin_listeleyebilir(self, admin_client, uretim_paleti_olusturuldu):
        r = admin_client.get("/api/uretim-paletleri/")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_depocu_listeleyebilir(self, depocu_client, uretim_paleti_olusturuldu):
        r = depocu_client.get("/api/uretim-paletleri/")
        assert r.status_code == 200

    def test_goruntuleyen_listeleyebilir(self, goruntuleyen_client, uretim_paleti_olusturuldu):
        r = goruntuleyen_client.get("/api/uretim-paletleri/")
        assert r.status_code == 200

    def test_tokensiz_401(self, client):
        r = client.get("/api/uretim-paletleri/")
        assert r.status_code == 401

    def test_yalnizca_uretim_kaynakli_gelir(self, admin_client, db_session, staging_raf):
        lot = LotFactory.create()
        # irsaliye kaynaklı — görünmemeli
        PaletFactory.create(
            palet_no="PLT-IRSALIYE-001",
            lot=lot,
            raf=staging_raf,
            kaynak="irsaliye",
            durum=UretimPaletDurum.YERLESTIRILDI,
        )
        PaletFactory.create(
            palet_no=PRD_NO,
            lot=lot,
            raf=staging_raf,
            kaynak="uretim",
            durum=UretimPaletDurum.OLUSTURULDU,
        )
        r = admin_client.get("/api/uretim-paletleri/")
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["palet_no"] == PRD_NO

    def test_durum_filtresi(self, admin_client, db_session, staging_raf):
        lot = LotFactory.create()
        PaletFactory.create(
            palet_no="PRD-A",
            lot=lot,
            raf=staging_raf,
            kaynak="uretim",
            durum=UretimPaletDurum.OLUSTURULDU,
        )
        PaletFactory.create(
            palet_no="PRD-B",
            lot=lot,
            raf=staging_raf,
            kaynak="uretim",
            durum=UretimPaletDurum.KABUL_EDILDI,
        )
        r = admin_client.get(f"/api/uretim-paletleri/?durum={UretimPaletDurum.OLUSTURULDU}")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 1
        assert data[0]["durum"] == UretimPaletDurum.OLUSTURULDU


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/uretim-paletleri/{palet_no}  — getir
# ─────────────────────────────────────────────────────────────────────────────

class TestUretimPaletiGetir:
    def test_admin_getirebilir(self, admin_client, uretim_paleti_olusturuldu):
        r = admin_client.get(f"/api/uretim-paletleri/{PRD_NO}")
        assert r.status_code == 200
        assert r.json()["palet_no"] == PRD_NO
        assert r.json()["kaynak"] == "uretim"

    def test_goruntuleyen_getirebilir(self, goruntuleyen_client, uretim_paleti_olusturuldu):
        r = goruntuleyen_client.get(f"/api/uretim-paletleri/{PRD_NO}")
        assert r.status_code == 200

    def test_olmayan_palet_404(self, admin_client):
        r = admin_client.get("/api/uretim-paletleri/PRD-YANLISNO")
        assert r.status_code == 404

    def test_irsaliye_palet_getirme_404(self, admin_client, db_session, staging_raf):
        """İrsaliye kaynaklı palet üretim endpoint'inden 404 dönmeli."""
        lot = LotFactory.create()
        PaletFactory.create(
            palet_no="PLT-IRSALIYE-002",
            lot=lot,
            raf=staging_raf,
            kaynak="irsaliye",
            durum=UretimPaletDurum.YERLESTIRILDI,
        )
        r = admin_client.get("/api/uretim-paletleri/PLT-IRSALIYE-002")
        assert r.status_code == 404

    def test_tokensiz_401(self, client):
        r = client.get(f"/api/uretim-paletleri/{PRD_NO}")
        assert r.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/uretim-paletleri/  — oluştur
# ─────────────────────────────────────────────────────────────────────────────

class TestUretimPaletiOlustur:
    def test_admin_olusturabilir(self, admin_client, db_session):
        depo = DepoFactory.create()
        RafFactory.create(depo=depo, is_staging=True)
        lot = LotFactory.create()

        r = admin_client.post("/api/uretim-paletleri/", json={
            "lot_id": lot.id,
            "koli_adedi": 48,
            "depo_id": depo.id,
        })

        assert r.status_code == 201
        data = r.json()
        assert data["kaynak"] == "uretim"
        assert data["durum"] == UretimPaletDurum.OLUSTURULDU
        assert data["koli_adedi"] == 48
        assert data["palet_no"].startswith("PRD-")

    def test_depocu_olusturabilir(self, depocu_client, depocu_user, staging_raf, db_session):
        depocu, _ = depocu_user
        lot = LotFactory.create()

        r = depocu_client.post("/api/uretim-paletleri/", json={
            "lot_id": lot.id,
            "koli_adedi": 24,
            "depo_id": depocu.depo_id,
        })

        assert r.status_code == 201

    def test_goruntuleyen_olusturamaz(self, goruntuleyen_client, db_session):
        lot = LotFactory.create()
        r = goruntuleyen_client.post("/api/uretim-paletleri/", json={
            "lot_id": lot.id,
            "koli_adedi": 10,
            "depo_id": 1,
        })
        assert r.status_code in (403, 422)

    def test_olmayan_lot_422_ya_da_404(self, admin_client, db_session):
        depo = DepoFactory.create()
        RafFactory.create(depo=depo, is_staging=True)
        r = admin_client.post("/api/uretim-paletleri/", json={
            "lot_id": 99999,
            "koli_adedi": 10,
            "depo_id": depo.id,
        })
        assert r.status_code in (404, 422)

    def test_staging_raf_yoksa_hata(self, admin_client, db_session):
        depo = DepoFactory.create()
        lot = LotFactory.create()
        # staging raf oluşturulmadı
        r = admin_client.post("/api/uretim-paletleri/", json={
            "lot_id": lot.id,
            "koli_adedi": 10,
            "depo_id": depo.id,
        })
        assert r.status_code in (400, 422, 500)

    def test_tokensiz_401(self, client, db_session):
        lot = LotFactory.create()
        r = client.post("/api/uretim-paletleri/", json={"lot_id": lot.id, "koli_adedi": 10})
        assert r.status_code == 401


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/uretim-paletleri/{palet_no}/kabul-bekle
# ─────────────────────────────────────────────────────────────────────────────

class TestUretimPaletiKabulBekle:
    def test_admin_kabul_bekleye_alabilir(self, admin_client, uretim_paleti_olusturuldu):
        r = admin_client.post(f"/api/uretim-paletleri/{PRD_NO}/kabul-bekle")
        assert r.status_code == 200
        assert r.json()["durum"] == UretimPaletDurum.KABUL_BEKLIYOR

    def test_depocu_kabul_bekleye_alabilir(self, depocu_client, uretim_paleti_olusturuldu):
        r = depocu_client.post(f"/api/uretim-paletleri/{PRD_NO}/kabul-bekle")
        assert r.status_code == 200

    def test_goruntuleyen_yetkisiz(self, goruntuleyen_client, uretim_paleti_olusturuldu):
        r = goruntuleyen_client.post(f"/api/uretim-paletleri/{PRD_NO}/kabul-bekle")
        assert r.status_code == 403

    def test_olmayan_palet_404(self, admin_client):
        r = admin_client.post("/api/uretim-paletleri/PRD-YANLISNO/kabul-bekle")
        assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/uretim-paletleri/{palet_no}/kabul-et
# ─────────────────────────────────────────────────────────────────────────────

class TestUretimPaletiKabulEt:
    def test_admin_kabul_edebilir(self, admin_client, uretim_paleti_kabul_bekliyor):
        r = admin_client.post(f"/api/uretim-paletleri/{PRD_NO}/kabul-et")
        assert r.status_code == 200
        data = r.json()
        # Otomatik geçiş: KABUL_EDILDI → YERLESTIRME_BEKLIYOR
        assert data["durum"] == UretimPaletDurum.YERLESTIRME_BEKLIYOR
        assert data["kabul_tarihi"] is not None
        assert data["yerlestirme_bekliyor"] is True

    def test_depocu_kabul_edebilir(self, depocu_client, uretim_paleti_kabul_bekliyor):
        r = depocu_client.post(f"/api/uretim-paletleri/{PRD_NO}/kabul-et")
        assert r.status_code == 200

    def test_goruntuleyen_yetkisiz(self, goruntuleyen_client, uretim_paleti_kabul_bekliyor):
        r = goruntuleyen_client.post(f"/api/uretim-paletleri/{PRD_NO}/kabul-et")
        assert r.status_code == 403

    def test_tc002_cift_kabul_reddedilir(self, admin_client, uretim_paleti_kabul_edildi):
        """TC-002: Zaten KABUL_EDILDI durumundaki paleti tekrar kabul-et → hata."""
        r = admin_client.post(f"/api/uretim-paletleri/{PRD_NO}/kabul-et")
        assert r.status_code in (400, 409, 422)

    def test_olmayan_palet_404(self, admin_client):
        r = admin_client.post("/api/uretim-paletleri/PRD-YANLISNO/kabul-et")
        assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/uretim-paletleri/{palet_no}/karantina
# ─────────────────────────────────────────────────────────────────────────────

class TestUretimPaletiKarantinaAl:
    def test_admin_karantinaya_alabilir(self, admin_client, uretim_paleti_kabul_edildi):
        r = admin_client.post(
            f"/api/uretim-paletleri/{PRD_NO}/karantina",
            json={"palet_no": PRD_NO, "sebep": "Hasar tespit edildi"},
        )
        assert r.status_code == 200
        assert r.json()["durum"] == UretimPaletDurum.KARANTINA

    def test_depocu_karantinaya_alabilir(self, depocu_client, uretim_paleti_kabul_edildi):
        r = depocu_client.post(
            f"/api/uretim-paletleri/{PRD_NO}/karantina",
            json={"palet_no": PRD_NO, "sebep": "Kalite sorunu"},
        )
        assert r.status_code == 200

    def test_kalite_departmani_karantinaya_alabilir(
        self, kalite_client, uretim_paleti_kabul_edildi
    ):
        r = kalite_client.post(
            f"/api/uretim-paletleri/{PRD_NO}/karantina",
            json={"palet_no": PRD_NO, "sebep": "QC red"},
        )
        assert r.status_code == 200

    def test_goruntuleyen_karantinaya_alamaz(
        self, goruntuleyen_client, uretim_paleti_kabul_edildi
    ):
        r = goruntuleyen_client.post(
            f"/api/uretim-paletleri/{PRD_NO}/karantina",
            json={"palet_no": PRD_NO},
        )
        assert r.status_code == 403

    def test_olmayan_palet_404(self, admin_client):
        r = admin_client.post(
            "/api/uretim-paletleri/PRD-YANLISNO/karantina",
            json={"palet_no": "PRD-YANLISNO"},
        )
        assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/uretim-paletleri/{palet_no}/karantina-cikar
# ─────────────────────────────────────────────────────────────────────────────

class TestUretimPaletiKarantinaCikar:
    def test_admin_karantinadan_cikarabilir(self, admin_client, uretim_paleti_karantina):
        """TC-005: KARANTINA → KABUL_EDILDI (yetkili admin) başarılı."""
        r = admin_client.post(
            f"/api/uretim-paletleri/{PRD_NO}/karantina-cikar",
            json={"palet_no": PRD_NO, "sebep": "QC onaylandı"},
        )
        assert r.status_code == 200
        assert r.json()["durum"] == UretimPaletDurum.KABUL_EDILDI

    def test_kalite_departmani_karantinadan_cikarabilir(
        self, kalite_client, uretim_paleti_karantina
    ):
        r = kalite_client.post(
            f"/api/uretim-paletleri/{PRD_NO}/karantina-cikar",
            json={"palet_no": PRD_NO},
        )
        assert r.status_code == 200

    def test_depocu_karantinadan_cikaramaz(self, depocu_client, uretim_paleti_karantina):
        """TC-006: KARANTINA → KABUL_EDILDI (yetkisiz depocu) → red."""
        r = depocu_client.post(
            f"/api/uretim-paletleri/{PRD_NO}/karantina-cikar",
            json={"palet_no": PRD_NO},
        )
        assert r.status_code in (403, 422)

    def test_goruntuleyen_karantinadan_cikaramaz(
        self, goruntuleyen_client, uretim_paleti_karantina
    ):
        r = goruntuleyen_client.post(
            f"/api/uretim-paletleri/{PRD_NO}/karantina-cikar",
            json={"palet_no": PRD_NO},
        )
        assert r.status_code in (403, 422)


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/uretim-paletleri/{palet_no}/iptal
# ─────────────────────────────────────────────────────────────────────────────

class TestUretimPaletiIptal:
    def test_admin_iptal_edebilir(self, admin_client, uretim_paleti_olusturuldu):
        r = admin_client.post(
            f"/api/uretim-paletleri/{PRD_NO}/iptal",
            json={"palet_no": PRD_NO, "sebep": "Hatalı etiket"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["durum"] == UretimPaletDurum.IPTAL_EDILDI
        assert data["aktif"] is False

    def test_depocu_iptal_edemez(self, depocu_client, uretim_paleti_olusturuldu):
        r = depocu_client.post(
            f"/api/uretim-paletleri/{PRD_NO}/iptal",
            json={"palet_no": PRD_NO, "sebep": "Test"},
        )
        assert r.status_code == 403

    def test_goruntuleyen_iptal_edemez(self, goruntuleyen_client, uretim_paleti_olusturuldu):
        r = goruntuleyen_client.post(
            f"/api/uretim-paletleri/{PRD_NO}/iptal",
            json={"palet_no": PRD_NO, "sebep": "Test"},
        )
        assert r.status_code == 403

    def test_sebep_bos_gecersiz(self, admin_client, uretim_paleti_olusturuldu):
        r = admin_client.post(
            f"/api/uretim-paletleri/{PRD_NO}/iptal",
            json={"palet_no": PRD_NO, "sebep": ""},
        )
        assert r.status_code == 422

    def test_olmayan_palet_404(self, admin_client):
        r = admin_client.post(
            "/api/uretim-paletleri/PRD-YANLISNO/iptal",
            json={"palet_no": "PRD-YANLISNO", "sebep": "test"},
        )
        assert r.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/uretim-paletleri/{palet_no}/yerlestirme-bekle
# ─────────────────────────────────────────────────────────────────────────────

class TestUretimPaletiYerlestirmeBekle:
    def test_admin_yerlestirme_bekleye_alabilir(
        self, admin_client, uretim_paleti_kabul_edildi
    ):
        r = admin_client.post(f"/api/uretim-paletleri/{PRD_NO}/yerlestirme-bekle")
        assert r.status_code == 200
        assert r.json()["durum"] == UretimPaletDurum.YERLESTIRME_BEKLIYOR

    def test_depocu_yerlestirme_bekleye_alabilir(
        self, depocu_client, uretim_paleti_kabul_edildi
    ):
        r = depocu_client.post(f"/api/uretim-paletleri/{PRD_NO}/yerlestirme-bekle")
        assert r.status_code == 200

    def test_goruntuleyen_yetkisiz(self, goruntuleyen_client, uretim_paleti_kabul_edildi):
        r = goruntuleyen_client.post(f"/api/uretim-paletleri/{PRD_NO}/yerlestirme-bekle")
        assert r.status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/uretim-paletleri/{palet_no}/yerlestir
# ─────────────────────────────────────────────────────────────────────────────

class TestUretimPaletiYerlestir:
    def test_admin_yerlestirme_yapabilir(
        self, admin_client, uretim_paleti_yerlestirme_bekliyor, db_session
    ):
        depo = DepoFactory.create()
        hedef_raf = RafFactory.create(depo=depo)

        r = admin_client.post(
            f"/api/uretim-paletleri/{PRD_NO}/yerlestir",
            json={"palet_no": PRD_NO, "raf_id": hedef_raf.id},
        )
        assert r.status_code == 200
        assert r.json()["durum"] == UretimPaletDurum.YERLESTIRILDI

    def test_depocu_yerlestirme_yapabilir(
        self, depocu_client, uretim_paleti_yerlestirme_bekliyor, db_session
    ):
        depo = DepoFactory.create()
        hedef_raf = RafFactory.create(depo=depo)

        r = depocu_client.post(
            f"/api/uretim-paletleri/{PRD_NO}/yerlestir",
            json={"palet_no": PRD_NO, "raf_id": hedef_raf.id},
        )
        assert r.status_code == 200

    def test_goruntuleyen_yetkisiz(
        self, goruntuleyen_client, uretim_paleti_yerlestirme_bekliyor, db_session
    ):
        raf = RafFactory.create()
        r = goruntuleyen_client.post(
            f"/api/uretim-paletleri/{PRD_NO}/yerlestir",
            json={"palet_no": PRD_NO, "raf_id": raf.id},
        )
        assert r.status_code == 403


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/uretim-paletleri/{palet_no}/etiket
# ─────────────────────────────────────────────────────────────────────────────

class TestUretimPaletiEtiket:
    def test_admin_zpl_alabilir(self, admin_client, uretim_paleti_olusturuldu):
        r = admin_client.get(f"/api/uretim-paletleri/{PRD_NO}/etiket")
        assert r.status_code == 200
        assert "^XA" in r.text
        assert PRD_NO in r.text

    def test_depocu_zpl_alabilir(self, depocu_client, uretim_paleti_olusturuldu):
        r = depocu_client.get(f"/api/uretim-paletleri/{PRD_NO}/etiket")
        assert r.status_code == 200

    def test_goruntuleyen_zpl_alabilir(self, goruntuleyen_client, uretim_paleti_olusturuldu):
        r = goruntuleyen_client.get(f"/api/uretim-paletleri/{PRD_NO}/etiket")
        assert r.status_code == 200

    def test_tokensiz_401(self, client, uretim_paleti_olusturuldu):
        r = client.get(f"/api/uretim-paletleri/{PRD_NO}/etiket")
        assert r.status_code == 401

    def test_olmayan_palet_404(self, admin_client):
        r = admin_client.get("/api/uretim-paletleri/PRD-YANLISNO/etiket")
        assert r.status_code == 404
