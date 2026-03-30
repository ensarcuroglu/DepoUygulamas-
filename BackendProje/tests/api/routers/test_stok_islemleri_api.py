"""
API testler: Stok Islemleri (Palet Bazli) endpoint'leri.
"""

import pytest
from tests.factories import (
    KullaniciFactory,
    MalKabulIrsaliyeFactory,
    MalKabulKalemiFactory,
    DepoFactory,
    UrunFactory,
    RafFactory,
    TedarikciFactory,
    PaletFactory,
    LotFactory,
)

pytestmark = pytest.mark.api


def _make_irsaliye_with_kalem(db_session, palet_no="PLT-2026-00500", durum="Bekliyor", **kalem_kw):
    """Irsaliye + kalem olusturur ve DB'ye yazar."""
    depo = DepoFactory.create(isim="Test Depo")
    tedarikci = TedarikciFactory.create()
    urun = UrunFactory.create(isim="Test Urun", barkod="8690000000001")

    irsaliye = MalKabulIrsaliyeFactory.create(
        depo=depo, tedarikci=tedarikci, durum="Onaylandi",
    )
    kalem = MalKabulKalemiFactory.create(
        irsaliye=irsaliye,
        palet_no=palet_no,
        urun=urun,
        lot_no="LOT-2026-0100",
        miktar=100,
        durum=durum,
        **kalem_kw,
    )
    db_session.commit()
    return depo, urun, irsaliye, kalem


# ══════════════════════════════════════════
# GET /api/stok-islemleri/palet/{palet_no}
# ══════════════════════════════════════════

class TestPaletSorgula:

    def test_bulunan_palet(self, admin_client, db_session):
        _make_irsaliye_with_kalem(db_session, palet_no="PLT-2026-00500")

        resp = admin_client.get("/api/stok-islemleri/palet/PLT-2026-00500")

        assert resp.status_code == 200
        data = resp.json()
        assert data["palet_no"] == "PLT-2026-00500"
        assert data["miktar"] == 100
        assert data["kaynak"] == "irsaliye"

    def test_bulunamayan_palet(self, admin_client):
        resp = admin_client.get("/api/stok-islemleri/palet/PLT-YOK-99999")
        assert resp.status_code == 404

    def test_yetkisiz_erisim(self, client):
        resp = client.get("/api/stok-islemleri/palet/PLT-2026-00500")
        assert resp.status_code == 401


# ══════════════════════════════════════════
# POST /api/stok-islemleri/palet-giris
# ══════════════════════════════════════════

class TestPaletGiris:

    def test_basarili_giris(self, admin_client, db_session):
        _make_irsaliye_with_kalem(db_session, palet_no="PLT-2026-00600")

        resp = admin_client.post(
            "/api/stok-islemleri/palet-giris",
            json={"palet_no": "PLT-2026-00600"},
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["hareket_tipi"] == "giris"
        assert data["miktar"] == 100

    def test_cift_giris_engeli(self, admin_client, db_session):
        _make_irsaliye_with_kalem(db_session, palet_no="PLT-2026-00700")

        # Ilk giris
        resp1 = admin_client.post(
            "/api/stok-islemleri/palet-giris",
            json={"palet_no": "PLT-2026-00700"},
        )
        assert resp1.status_code == 201

        # Ikinci giris — zaten giris yapilmis
        resp2 = admin_client.post(
            "/api/stok-islemleri/palet-giris",
            json={"palet_no": "PLT-2026-00700"},
        )
        assert resp2.status_code in (400, 409)

    def test_yetkisiz_depo(self, depocu_client, depocu_user, db_session):
        """Depocu farkli depoya atanmis, baska deponun paletine giris yapmaya calisiyor."""
        user_orm, _ = depocu_user
        baska_depo = DepoFactory.create(isim="Baska Depo")

        # Kullanicinin depo_id'sini farkli bir depoya ata
        kullanici_depo = DepoFactory.create(isim="Kullanici Deposu")
        user_orm.depo_id = kullanici_depo.id
        db_session.commit()

        tedarikci = TedarikciFactory.create()
        urun = UrunFactory.create()
        irsaliye = MalKabulIrsaliyeFactory.create(
            depo=baska_depo, tedarikci=tedarikci,
        )
        MalKabulKalemiFactory.create(
            irsaliye=irsaliye,
            palet_no="PLT-2026-00800",
            urun=urun,
            miktar=50,
        )
        db_session.commit()

        resp = depocu_client.post(
            "/api/stok-islemleri/palet-giris",
            json={"palet_no": "PLT-2026-00800"},
        )
        assert resp.status_code == 403

    def test_bos_palet_no_reddedilir(self, admin_client):
        resp = admin_client.post(
            "/api/stok-islemleri/palet-giris",
            json={"palet_no": "   "},
        )
        assert resp.status_code == 422


# ══════════════════════════════════════════
# POST /api/stok-islemleri/palet-cikis
# ══════════════════════════════════════════

class TestPaletCikis:

    def _giris_yap(self, admin_client, db_session, palet_no="PLT-2026-00900"):
        """Oncelikle palet girisi yap (cikis icin hazirlik)."""
        _make_irsaliye_with_kalem(db_session, palet_no=palet_no)
        resp = admin_client.post(
            "/api/stok-islemleri/palet-giris",
            json={"palet_no": palet_no},
        )
        assert resp.status_code == 201
        return resp.json()

    def test_tam_cikis(self, admin_client, db_session):
        self._giris_yap(admin_client, db_session, "PLT-2026-00900")

        resp = admin_client.post(
            "/api/stok-islemleri/palet-cikis",
            json={"palet_no": "PLT-2026-00900"},
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["hareket_tipi"] == "cikis"
        assert data["miktar"] == 100

    def test_kismi_cikis(self, admin_client, db_session):
        self._giris_yap(admin_client, db_session, "PLT-2026-01000")

        resp = admin_client.post(
            "/api/stok-islemleri/palet-cikis",
            json={"palet_no": "PLT-2026-01000", "miktar": 30},
        )

        assert resp.status_code == 201
        assert resp.json()["miktar"] == 30

    def test_bos_palet_cikis(self, admin_client, db_session):
        """Tam cikis yapilmis palet tekrar cikis yapilamaz."""
        self._giris_yap(admin_client, db_session, "PLT-2026-01100")

        # Tam cikis
        resp1 = admin_client.post(
            "/api/stok-islemleri/palet-cikis",
            json={"palet_no": "PLT-2026-01100"},
        )
        assert resp1.status_code == 201

        # Bos paletten tekrar cikis
        resp2 = admin_client.post(
            "/api/stok-islemleri/palet-cikis",
            json={"palet_no": "PLT-2026-01100"},
        )
        assert resp2.status_code == 400

    def test_olmayan_palet_cikis(self, admin_client):
        resp = admin_client.post(
            "/api/stok-islemleri/palet-cikis",
            json={"palet_no": "PLT-YOK-99999"},
        )
        assert resp.status_code == 404
