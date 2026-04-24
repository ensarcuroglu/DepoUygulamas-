"""Router testleri: app.api.v1.routers.mobil_terminal.

Use-case/servis bağımlılıkları `app.dependency_overrides` ile mock'lanır.
DB gerekmez — sadece HTTP ↔ use-case kontratı ve rol/depo kısıtlaması test edilir.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from unittest.mock import MagicMock

from app.api.v1.routers import mobil_terminal as mobil_terminal_router
from app.application.dto.yerlestirme_gorevi_dto import (
    AlternatifRafDTO,
    YerlestirmeGoreviResponseDTO,
    YerlestirmeOnaylaSonucDTO,
)
from app.core.entities.yerlestirme_gorevi import GorevDurum, GorevTipi
from app.infrastructure.di.container import (
    get_kapasite_dogrulama_servisi,
    get_log_repo,
    get_lot_repo,
    get_palet_barkod_ile_getir_uc,
    get_palet_repo,
    get_raf_repo,
    get_urun_repo,
    get_yerlestirme_gorevi_listele_uc,
    get_yerlestirme_gorevi_repo,
    get_yerlestirme_onayla_uc,
    get_zon_repo,
)
from main import app

pytestmark = pytest.mark.api


# ─────────────────────────────────────────
# Yardımcılar
# ─────────────────────────────────────────

def _set_override(dep, value):
    app.dependency_overrides[dep] = lambda: value


def _palet_stub(*, id=1, palet_no="PRD-20260424-001", aktif=True, lot_id=10, raf_id=20, koli_adedi=50, palet_kg=120.0):
    return SimpleNamespace(
        id=id, palet_no=palet_no, aktif=aktif, lot_id=lot_id,
        raf_id=raf_id, koli_adedi=koli_adedi, palet_kg=palet_kg,
    )


def _gorev_dto(
    *,
    id: int = 1,
    palet_id: int = 1,
    durum: str = GorevDurum.ATANDI,
    atanan_kullanici_id: int = 2,
    tamamlanma_tarihi=None,
) -> YerlestirmeGoreviResponseDTO:
    return YerlestirmeGoreviResponseDTO(
        id=id,
        palet_id=palet_id,
        mal_kabul_irsaliye_id=None,
        depo_id=7,
        tip=GorevTipi.YERLESTIRME,
        kaynak_raf_id=None,
        onerilen_raf_id=20,
        gerceklesen_raf_id=None,
        durum=durum,
        oncelik=3,
        atanan_kullanici_id=atanan_kullanici_id,
        override_kullanici_id=None,
        override_neden=None,
        olusturma_tarihi=datetime(2026, 4, 1),
        baslama_tarihi=None,
        tamamlanma_tarihi=tamamlanma_tarihi,
        iptal_nedeni=None,
        onerilen_raf_farkli=False,
    )


# ─────────────────────────────────────────
# POST /api/terminal/scan/palet
# ─────────────────────────────────────────

class TestScanPalet:
    def test_anonim_401(self, anon_client):
        resp = anon_client.post("/api/terminal/scan/palet", json={"palet_barkod": "PRD-20260424-001"})
        assert resp.status_code == 401

    def test_happy_path_lot_ve_raf_zenginlestirir(self, client, depocu_user):
        palet = _palet_stub(palet_no="PRD-20260424-001")
        uc = MagicMock()
        uc.execute.return_value = palet
        lot_repo = MagicMock()
        lot_repo.getir_id_ile.return_value = SimpleNamespace(lot_no="LOT-1", urun_id=501)
        urun_repo = MagicMock()
        urun_repo.getir_id_ile.return_value = SimpleNamespace(ad="Süt 1L")
        raf_repo = MagicMock()
        raf_repo.getir_id_ile.return_value = SimpleNamespace(kod="GNL-A-01-01-01")

        _set_override(get_palet_barkod_ile_getir_uc, uc)
        _set_override(get_lot_repo, lot_repo)
        _set_override(get_urun_repo, urun_repo)
        _set_override(get_raf_repo, raf_repo)

        resp = client.post("/api/terminal/scan/palet", json={"palet_barkod": "PRD-20260424-001"})

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["palet_no"] == "PRD-20260424-001"
        assert data["lot_no"] == "LOT-1"
        assert data["urun_adi"] == "Süt 1L"
        assert data["raf_kod"] == "GNL-A-01-01-01"
        uc.execute.assert_called_once_with("PRD-20260424-001")

    def test_palet_yok_404(self, client, depocu_user):
        from app.core.exceptions import KayitBulunamadiError

        uc = MagicMock()
        uc.execute.side_effect = KayitBulunamadiError("Palet", "PRD-20260424-999")
        _set_override(get_palet_barkod_ile_getir_uc, uc)
        _set_override(get_lot_repo, MagicMock())
        _set_override(get_urun_repo, MagicMock())
        _set_override(get_raf_repo, MagicMock())

        resp = client.post("/api/terminal/scan/palet", json={"palet_barkod": "PRD-20260424-999"})
        assert resp.status_code == 404

    def test_bos_barkod_422(self, client, depocu_user):
        _set_override(get_palet_barkod_ile_getir_uc, MagicMock())
        _set_override(get_lot_repo, MagicMock())
        _set_override(get_urun_repo, MagicMock())
        _set_override(get_raf_repo, MagicMock())
        resp = client.post("/api/terminal/scan/palet", json={"palet_barkod": ""})
        assert resp.status_code == 422


# ─────────────────────────────────────────
# POST /api/terminal/scan/raf
# ─────────────────────────────────────────

class TestScanRaf:
    def _setup_ok(self, *, raf_kapasite=10, palet_sayisi=3):
        raf = SimpleNamespace(
            id=20, kod="GNL-A-01-01-01", zon_id=55, kapasite=raf_kapasite, max_agirlik_kg=1000.0,
        )
        raf_repo = MagicMock()
        raf_repo.getir_kod_ile.return_value = raf
        zon_repo = MagicMock()
        zon_repo.getir_id_ile.return_value = SimpleNamespace(isim="Genel", tip="Genel")
        palet_repo = MagicMock()
        palet_repo.getir_hepsi.return_value = [
            _palet_stub(id=i, palet_kg=100.0) for i in range(palet_sayisi)
        ]
        _set_override(get_raf_repo, raf_repo)
        _set_override(get_zon_repo, zon_repo)
        _set_override(get_palet_repo, palet_repo)
        return raf_repo, zon_repo, palet_repo

    def test_depocu_kendi_deposuyla_sorgular(self, client, depocu_user):
        raf_repo, *_ = self._setup_ok(raf_kapasite=10, palet_sayisi=3)

        resp = client.post("/api/terminal/scan/raf", json={"raf_barkod": "GNL-A-01-01-01"})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["raf_id"] == 20
        assert data["mevcut_palet_sayisi"] == 3
        assert data["bos_slot"] == 7
        assert data["mevcut_agirlik_kg"] == 300.0
        # Depocu'nun depo_id'si (7) iletildi
        raf_repo.getir_kod_ile.assert_called_once_with("GNL-A-01-01-01", 7)

    def test_depocu_depo_id_override_edemez(self, client, depocu_user):
        """Depocu body'de depo_id gönderse de kendi deposu kullanılır."""
        raf_repo, *_ = self._setup_ok()
        resp = client.post(
            "/api/terminal/scan/raf",
            json={"raf_barkod": "GNL-A-01-01-01", "depo_id": 999},
        )
        assert resp.status_code == 200
        raf_repo.getir_kod_ile.assert_called_once_with("GNL-A-01-01-01", 7)

    def test_admin_body_depo_id_kullanilir(self, client, admin_user):
        raf_repo, *_ = self._setup_ok()
        resp = client.post(
            "/api/terminal/scan/raf",
            json={"raf_barkod": "GNL-A-01-01-01", "depo_id": 42},
        )
        assert resp.status_code == 200
        raf_repo.getir_kod_ile.assert_called_once_with("GNL-A-01-01-01", 42)

    def test_raf_yok_404(self, client, depocu_user):
        raf_repo = MagicMock(); raf_repo.getir_kod_ile.return_value = None
        _set_override(get_raf_repo, raf_repo)
        _set_override(get_zon_repo, MagicMock())
        _set_override(get_palet_repo, MagicMock())

        resp = client.post("/api/terminal/scan/raf", json={"raf_barkod": "GNL-A-99-99-99"})
        assert resp.status_code == 404

    def test_depocu_depo_atanmamis_400(self, client, override_user):
        """Depo atanmamış depocuya anlamlı hata döner."""
        override_user(SimpleNamespace(
            id=2, rol="depocu", depo_id=None, depo_erisimi_yok=False,
            kullanici_adi="d", ad_soyad="d", sifre_hash="x",
            telefon=None, email=None, departman=None, sicil_no=None,
            kart_numarasi=None, refresh_token_hash=None,
            refresh_token_son_kullanim=None, olusturma_tarihi=datetime(2026, 1, 1),
        ))
        _set_override(get_raf_repo, MagicMock())
        _set_override(get_zon_repo, MagicMock())
        _set_override(get_palet_repo, MagicMock())

        resp = client.post("/api/terminal/scan/raf", json={"raf_barkod": "GNL-A-01-01-01"})
        assert resp.status_code == 400
        assert "depo" in resp.json()["error"].lower()


# ─────────────────────────────────────────
# POST /api/terminal/yerlestir
# ─────────────────────────────────────────

class TestYerlestir:
    def _base_setup(self, palet_no="PRD-20260424-001", depo_id=7):
        gorev_orm = SimpleNamespace(id=5, palet_id=1, depo_id=depo_id)
        palet = _palet_stub(id=1, palet_no=palet_no)
        gorev_repo = MagicMock(); gorev_repo.getir_id_ile.return_value = gorev_orm
        palet_repo = MagicMock(); palet_repo.getir_id_ile.return_value = palet
        uc = MagicMock()
        uc.execute.return_value = YerlestirmeOnaylaSonucDTO(
            basarili=True, durum="TAMAMLANDI", palet_no=palet_no,
            raf_kod="GNL-A-01-01-01", mesaj="ok", gorev=_gorev_dto(id=5, durum=GorevDurum.TAMAMLANDI),
        )
        _set_override(get_yerlestirme_gorevi_repo, gorev_repo)
        _set_override(get_palet_repo, palet_repo)
        _set_override(get_yerlestirme_onayla_uc, uc)
        return gorev_repo, palet_repo, uc

    def test_happy_path_use_case_dogru_parametrelerle_cagrilir(self, client, depocu_user):
        _, _, uc = self._base_setup(palet_no="PRD-20260424-001")
        body = {"gorev_id": 5, "palet_barkod": "PRD-20260424-001", "raf_barkod": "GNL-A-01-01-01"}

        resp = client.post("/api/terminal/yerlestir", json=body)

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["basarili"] is True
        assert data["durum"] == "TAMAMLANDI"
        # kullanici_id depocu id'si 2 olacak
        call_args = uc.execute.call_args
        assert call_args.args[0] == 5
        assert call_args.args[1].okutulan_raf_kodu == "GNL-A-01-01-01"
        assert call_args.kwargs["kullanici_id"] == 2

    def test_idempotency_cache_hit_use_case_cagrilmaz(self, client, depocu_user, monkeypatch):
        gorev_repo, palet_repo, uc = self._base_setup(palet_no="PRD-20260424-001")
        cached = {
            "basarili": True,
            "durum": "TAMAMLANDI",
            "palet_no": "PRD-20260424-001",
            "raf_kod": "GNL-A-01-01-01",
            "mesaj": "cached",
        }
        monkeypatch.setattr(
            mobil_terminal_router,
            "idempotency_kontrol",
            lambda db, key, endpoint: cached,
        )

        resp = client.post(
            "/api/terminal/yerlestir",
            headers={"Idempotency-Key": "scan-test"},
            json={
                "gorev_id": 5,
                "palet_barkod": "PRD-20260424-001",
                "raf_barkod": "GNL-A-01-01-01",
            },
        )

        assert resp.status_code == 200, resp.text
        assert resp.json()["mesaj"] == "cached"
        gorev_repo.getir_id_ile.assert_not_called()
        palet_repo.getir_id_ile.assert_not_called()
        uc.execute.assert_not_called()

    def test_gorev_yok_404(self, client, depocu_user):
        gorev_repo = MagicMock(); gorev_repo.getir_id_ile.return_value = None
        _set_override(get_yerlestirme_gorevi_repo, gorev_repo)
        _set_override(get_palet_repo, MagicMock())
        _set_override(get_yerlestirme_onayla_uc, MagicMock())

        resp = client.post(
            "/api/terminal/yerlestir",
            json={"gorev_id": 9, "palet_barkod": "PRD-20260424-001", "raf_barkod": "GNL-A-01-01-01"},
        )
        assert resp.status_code == 404

    def test_palet_barkod_eslesmezse_400(self, client, depocu_user):
        self._base_setup(palet_no="PRD-20260424-001")
        resp = client.post(
            "/api/terminal/yerlestir",
            json={"gorev_id": 5, "palet_barkod": "PRD-20260424-002", "raf_barkod": "GNL-A-01-01-01"},
        )
        assert resp.status_code == 400
        assert "eşleşmiyor" in resp.json()["error"]

    def test_depocu_farkli_depoya_gorev_reddedilir(self, client, depocu_user):
        # Görev farklı depoda (999), depocu 7'de
        self._base_setup(palet_no="PRD-20260424-001", depo_id=999)
        resp = client.post(
            "/api/terminal/yerlestir",
            json={"gorev_id": 5, "palet_barkod": "PRD-20260424-001", "raf_barkod": "GNL-A-01-01-01"},
        )
        assert resp.status_code == 400
        assert "farklı" in resp.json()["error"]


# ─────────────────────────────────────────
# GET /api/terminal/gorevlerim
# ─────────────────────────────────────────

class TestGorevlerim:
    def test_atandi_ve_devameden_birlestirilir_duplicate_filtreli(self, client, depocu_user):
        g_atandi = _gorev_dto(id=1, atanan_kullanici_id=2, durum=GorevDurum.ATANDI)
        g_devam = _gorev_dto(id=2, atanan_kullanici_id=2, durum=GorevDurum.DEVAM_EDIYOR)
        g_duplicate = _gorev_dto(id=1, atanan_kullanici_id=2, durum=GorevDurum.DEVAM_EDIYOR)

        uc = MagicMock()
        # İlk çağrı "Atandi" için g_atandi, ikinci "DevamEdiyor" için (g_devam, g_duplicate)
        uc.execute.side_effect = [[g_atandi], [g_devam, g_duplicate]]
        _set_override(get_yerlestirme_gorevi_listele_uc, uc)

        resp = client.get("/api/terminal/gorevlerim")

        assert resp.status_code == 200
        ids = [g["id"] for g in resp.json()]
        assert ids == [1, 2]  # duplicate id=1 filtrelendi
        # Depocu'nun depo_id'si her çağrıya iletildi
        for call in uc.execute.call_args_list:
            assert call.kwargs["depo_id"] == 7
            assert call.kwargs["atanan_kullanici_id"] == 2


# ─────────────────────────────────────────
# GET /api/terminal/ozet
# ─────────────────────────────────────────

class TestOzet:
    def test_bekleyen_atanan_ve_bugun_tamamlanan(self, client, depocu_user):
        bugun_aware = datetime.now(timezone.utc)
        uc = MagicMock()
        # Sırasıyla: "Bekliyor" listele, sonra Atandi, DevamEdiyor, Tamamlandi
        bekleyen_list = [_gorev_dto(id=10), _gorev_dto(id=11), _gorev_dto(id=12)]
        atanan_list = [_gorev_dto(id=1, atanan_kullanici_id=2)]
        devam_list = [_gorev_dto(id=2, atanan_kullanici_id=2)]
        tamamlanmis = [
            _gorev_dto(id=3, atanan_kullanici_id=2, tamamlanma_tarihi=bugun_aware),
            _gorev_dto(id=4, atanan_kullanici_id=99, tamamlanma_tarihi=bugun_aware),
            _gorev_dto(id=5, atanan_kullanici_id=2, tamamlanma_tarihi=datetime(2025, 1, 1, tzinfo=timezone.utc)),
        ]
        uc.execute.side_effect = [bekleyen_list, atanan_list, devam_list, tamamlanmis]
        _set_override(get_yerlestirme_gorevi_listele_uc, uc)

        resp = client.get("/api/terminal/ozet")

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["bekleyen_gorev"] == 3
        assert data["benim_atanan_gorev"] == 2
        # Bugün tamamlanan ve kullanıcı 2'ye ait: sadece id=3
        assert data["bugun_tamamlanan"] == 1
        assert data["kullanici_id"] == 2


# ─────────────────────────────────────────
# POST /api/terminal/alternatif-raf
# ─────────────────────────────────────────

class TestAlternatifRaf:
    def test_alternatifler_siralanmis_doner(self, client, depocu_user):
        alt_raf1 = SimpleNamespace(id=30, kod="D-01", kapasite=5)
        alt_raf2 = SimpleNamespace(id=31, kod="D-02", kapasite=10)
        kapasite_svc = MagicMock()
        kapasite_svc.alternatif_raflar_getir.return_value = [alt_raf1, alt_raf2]
        kapasite_svc.doluluk_orani.side_effect = [0.8, 0.4]
        palet_repo = MagicMock()
        palet_repo.getir_hepsi.side_effect = [
            [_palet_stub(id=i) for i in range(3)],  # alt_raf1 için 3 palet
            [_palet_stub(id=i) for i in range(2)],  # alt_raf2 için 2 palet
        ]
        _set_override(get_kapasite_dogrulama_servisi, kapasite_svc)
        _set_override(get_palet_repo, palet_repo)

        resp = client.post(
            "/api/terminal/alternatif-raf",
            json={"zon_id": 55, "palet_kg": 150.0, "limit": 5},
        )

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert [d["raf_id"] for d in data] == [30, 31]
        assert data[0]["bos_slot"] == 2  # 5 - 3
        assert data[1]["bos_slot"] == 8  # 10 - 2
        assert data[0]["skor"] == 80.0

    def test_bos_alternatif_bos_liste_doner(self, client, depocu_user):
        kapasite_svc = MagicMock()
        kapasite_svc.alternatif_raflar_getir.return_value = []
        _set_override(get_kapasite_dogrulama_servisi, kapasite_svc)
        _set_override(get_palet_repo, MagicMock())

        resp = client.post(
            "/api/terminal/alternatif-raf",
            json={"zon_id": 55, "palet_kg": 150.0, "limit": 5},
        )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_zon_id_zorunlu_422(self, client, depocu_user):
        _set_override(get_kapasite_dogrulama_servisi, MagicMock())
        _set_override(get_palet_repo, MagicMock())
        resp = client.post("/api/terminal/alternatif-raf", json={"palet_kg": 100.0})
        assert resp.status_code == 422


# ─────────────────────────────────────────
# POST /api/terminal/log-palet-hata
# ─────────────────────────────────────────

class TestPaletHataLogla:
    def test_204_ve_log_yazilir(self, client, depocu_user):
        log_repo = MagicMock()
        _set_override(get_log_repo, log_repo)

        resp = client.post(
            "/api/terminal/log-palet-hata",
            json={
                "palet_barkod": "P-1",
                "beklenen_palet_barkod": "P-2",
                "gorev_id": 99,
            },
        )

        assert resp.status_code == 204
        assert resp.content == b""
        log_repo.olustur.assert_called_once()
        # SistemLog entity detay alanı her üç bilgiyi de içermeli
        log_entity = log_repo.olustur.call_args.args[0]
        assert "okutulan=P-1" in log_entity.detay
        assert "beklenen=P-2" in log_entity.detay
        assert "gorev_id=99" in log_entity.detay

    def test_opsiyonel_alanlar_yoksa_yine_loglanir(self, client, depocu_user):
        log_repo = MagicMock()
        _set_override(get_log_repo, log_repo)
        resp = client.post(
            "/api/terminal/log-palet-hata",
            json={"palet_barkod": "P-1"},
        )
        assert resp.status_code == 204
        log_repo.olustur.assert_called_once()


# ─────────────────────────────────────────
# Rol bazlı erişim (mobil terminal tüm giriş yapmışlara açık)
# ─────────────────────────────────────────

class TestRolKontrolu:
    def test_lojistik_scan_palet_erisebilir(self, client, lojistik_user):
        uc = MagicMock()
        uc.execute.return_value = _palet_stub(lot_id=None, raf_id=None)
        _set_override(get_palet_barkod_ile_getir_uc, uc)
        _set_override(get_lot_repo, MagicMock())
        _set_override(get_urun_repo, MagicMock())
        _set_override(get_raf_repo, MagicMock())

        resp = client.post("/api/terminal/scan/palet", json={"palet_barkod": "PRD-20260424-001"})
        assert resp.status_code == 200
