import pytest

from tests.factories import (
    DepoFactory,
    MalKabulIrsaliyeFactory,
    MalKabulKalemiFactory,
    TedarikciFactory,
    UrunFactory,
)

pytestmark = pytest.mark.api


def _mal_kabul_irsaliyesi_olustur(db_session):
    depo = DepoFactory.create(isim="Mal Kabul Test Deposu")
    tedarikci = TedarikciFactory.create(firma_adi="Test Tedarikci")
    urun = UrunFactory.create(isim="Test Urun", barkod="8690000001001")
    irsaliye = MalKabulIrsaliyeFactory.create(
        depo=depo,
        tedarikci=tedarikci,
    )
    kalem = MalKabulKalemiFactory.create(
        irsaliye=irsaliye,
        urun=urun,
        palet_no="PLT-ISTISNA-0001",
        miktar=10,
    )
    db_session.commit()
    return irsaliye, kalem


class TestMalKabulKalemiIstisnaYetkileri:
    def test_depocu_istisna_bildirebilir(self, depocu_client, db_session):
        irsaliye, kalem = _mal_kabul_irsaliyesi_olustur(db_session)

        response = depocu_client.put(
            f"/api/mal-kabul-irsaliyeleri/{irsaliye.id}/kalemler/{kalem.id}/istisna",
            json={
                "istisna_tip": "Hasarlı",
                "istisna_aciklama": "Kutu ezik",
                "gerceklesen_miktar": 8,
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["istisna_sayisi"] == 1
        kalem_data = next(item for item in data["kalemler"] if item["id"] == kalem.id)
        assert kalem_data["istisna_tip"] == "Hasarlı"
        assert kalem_data["gerceklesen_miktar"] == 8

    @pytest.mark.parametrize(
        ("client_fixture", "expected_status"),
        [
            ("client", 401),
            ("lojistik_client", 403),
        ],
    )
    def test_admin_ve_depocu_disindakiler_istisna_bildiremez(
        self,
        client_fixture,
        expected_status,
        request,
        db_session,
    ):
        client = request.getfixturevalue(client_fixture)
        irsaliye, kalem = _mal_kabul_irsaliyesi_olustur(db_session)

        response = client.put(
            f"/api/mal-kabul-irsaliyeleri/{irsaliye.id}/kalemler/{kalem.id}/istisna",
            json={
                "istisna_tip": "Eksik",
            },
        )

        assert response.status_code == expected_status


class TestMalKabulIrsaliyeListeIstisnaOzeti:
    def test_liste_istisna_sayisini_ve_kalemleri_dondurur(self, admin_client, db_session):
        depo = DepoFactory.create(isim="Liste Test Deposu")
        tedarikci = TedarikciFactory.create(firma_adi="Liste Tedarikci")
        urun = UrunFactory.create(isim="Liste Urun", barkod="8690000001002")
        irsaliye = MalKabulIrsaliyeFactory.create(
            depo=depo,
            tedarikci=tedarikci,
        )
        MalKabulKalemiFactory.create(
            irsaliye=irsaliye,
            urun=urun,
            palet_no="PLT-LISTE-0001",
            miktar=12,
            istisna_tip="Hasarlı",
            istisna_aciklama="Ambalaj yirtik",
            gerceklesen_miktar=11,
        )
        MalKabulKalemiFactory.create(
            irsaliye=irsaliye,
            urun=urun,
            palet_no="PLT-LISTE-0002",
            miktar=6,
        )
        db_session.commit()

        response = admin_client.get("/api/mal-kabul-irsaliyeleri/")

        assert response.status_code == 200
        assert len(response.json()) == 1

        data = response.json()[0]
        assert data["istisna_sayisi"] == 1
        assert len(data["kalemler"]) == 2
        assert any(kalem["istisna_tip"] == "Hasarlı" for kalem in data["kalemler"])
