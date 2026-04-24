"""Router testleri: app.api.v1.routers.stok_islemleri.

Faz 2 — Mock-based. `get_palet_bazli_stok_service` ve
`get_palet_sorgulama_service` override edilir; `get_db` fake session ile
karşılanır. Idempotency cache davranışı monkeypatch ile test edilir.
"""

from __future__ import annotations

from datetime import date, datetime
from types import SimpleNamespace

import pytest
from unittest.mock import MagicMock
from sqlalchemy.exc import IntegrityError

from app.application.dto.palet_bilgi_dto import PaletBilgiDTO
from app.core.exceptions import KayitBulunamadiError, YetersizStokError
from app.infrastructure.di.container import (
    get_palet_bazli_stok_service,
    get_palet_sorgulama_service,
)
from main import app

pytestmark = pytest.mark.api


def _set_override(dep, value):
    app.dependency_overrides[dep] = lambda: value


def _hareket_stub(
    *,
    id: int = 10,
    urun_id: int = 501,
    lot_id: int | None = 55,
    palet_id: int | None = 100,
    hareket_tipi: str = "giris",
    miktar: int = 100,
    palet_no: str = "P-1",
    siparis_no: str | None = None,
):
    return SimpleNamespace(
        id=id, urun_id=urun_id, lot_id=lot_id, palet_id=palet_id,
        raf_id=20, hareket_tipi=hareket_tipi, miktar=miktar,
        siparis_no=siparis_no, irsaliye_no=None, tir_plaka=None,
        depo_kapi=None, sofor_adi=None, tasiyici_firma=None,
        barkodlar=None, aciklama="", kullanici_id=1,
        tarih=datetime(2026, 4, 20), palet_no=palet_no,
    )


def _palet_bilgi_stub(palet_no: str = "P-1", **over) -> PaletBilgiDTO:
    return PaletBilgiDTO(
        palet_no=palet_no,
        urun_id=over.get("urun_id", 501),
        urun_adi=over.get("urun_adi", "Süt 1L"),
        urun_barkod="8690",
        lot_no="LOT-1",
        lot_id=55,
        miktar=over.get("miktar", 100),
        raf_id=20,
        raf_bilgi="Depo-A / A-01",
        depo_id=7,
        depo_adi="Depo A",
        durum="aktif",
        kaynak=over.get("kaynak", "sistem"),
        son_kullanma_tarihi=date(2027, 1, 1),
        giris_yapildi_mi=True,
    )


def _integrity_error():
    return IntegrityError("INSERT ...", {}, Exception("duplicate"))


# ─────────────────────────────────────────
# GET /api/stok-islemleri/palet/{palet_no}
# ─────────────────────────────────────────

class TestPaletSorgula:
    def test_happy_path(self, client, depocu_user):
        svc = MagicMock()
        svc.sorgula.return_value = _palet_bilgi_stub(palet_no="PLT-100")
        _set_override(get_palet_sorgulama_service, svc)

        resp = client.get("/api/stok-islemleri/palet/PLT-100")

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["palet_no"] == "PLT-100"
        assert data["miktar"] == 100
        svc.sorgula.assert_called_once_with("PLT-100")

    def test_bulunamayan_palet_404(self, client, depocu_user):
        svc = MagicMock()
        svc.sorgula.side_effect = KayitBulunamadiError("Palet", "P-YOK")
        _set_override(get_palet_sorgulama_service, svc)

        resp = client.get("/api/stok-islemleri/palet/P-YOK")
        assert resp.status_code == 404

    def test_anonim_401(self, anon_client):
        resp = anon_client.get("/api/stok-islemleri/palet/PLT-1")
        assert resp.status_code == 401


# ─────────────────────────────────────────
# POST /api/stok-islemleri/palet-giris
# ─────────────────────────────────────────

class TestPaletGiris:
    def test_happy_path_201(self, client, depocu_user):
        svc = MagicMock()
        svc.palet_giris.return_value = _hareket_stub(palet_no="PLT-200")
        _set_override(get_palet_bazli_stok_service, svc)

        resp = client.post(
            "/api/stok-islemleri/palet-giris",
            json={"palet_no": "PLT-200"},
        )

        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["id"] == 10
        assert data["palet_no"] == "PLT-200"
        svc.palet_giris.assert_called_once()

    def test_palet_bulunamadi_404(self, client, depocu_user):
        svc = MagicMock()
        svc.palet_giris.side_effect = KayitBulunamadiError("Palet", "P-X")
        _set_override(get_palet_bazli_stok_service, svc)

        resp = client.post(
            "/api/stok-islemleri/palet-giris",
            json={"palet_no": "P-X"},
        )
        assert resp.status_code == 404

    def test_idempotency_cache_hit_dondurulur(self, client, depocu_user, monkeypatch):
        """Aynı Idempotency-Key ile ikinci istek → use-case çağrılmaz, cache dönülür."""
        cached_body = _hareket_stub(palet_no="PLT-CACHE").__dict__
        # from_entity ile dönecek body olarak tam dict gerek; StokHareketiResponseDTO
        # model_dump formatında olmalı. En kolay yol: önceki test runtime'ında kaydedilmiş
        # dict'i simüle edelim.
        cached_body = {
            "id": 99, "urun_id": 501, "lot_id": 55, "palet_id": 100, "raf_id": 20,
            "hareket_tipi": "giris", "miktar": 100, "siparis_no": None, "irsaliye_no": None,
            "tir_plaka": None, "depo_kapi": None, "sofor_adi": None, "tasiyici_firma": None,
            "barkodlar": None, "aciklama": "", "kullanici_id": 1,
            "tarih": "2026-04-20T00:00:00", "palet_no": "PLT-CACHE",
        }
        import app.api.v1.routers.stok_islemleri as router_mod
        monkeypatch.setattr(router_mod, "idempotency_kontrol", lambda db, k, e: cached_body)
        svc = MagicMock()
        _set_override(get_palet_bazli_stok_service, svc)

        resp = client.post(
            "/api/stok-islemleri/palet-giris",
            json={"palet_no": "PLT-CACHE"},
            headers={"Idempotency-Key": "req-123"},
        )
        assert resp.status_code == 201
        assert resp.json()["id"] == 99
        # Use-case hiç çağrılmadı
        svc.palet_giris.assert_not_called()

    def test_integrity_error_mevcut_hareketi_doner(self, client, depocu_user, monkeypatch):
        """Duplicate key → rollback + son_hareketi_getir_palet_ile yanıtı."""
        svc = MagicMock()
        svc.palet_giris.side_effect = _integrity_error()
        svc.son_hareketi_getir_palet_ile.return_value = _hareket_stub(id=77, palet_no="PLT-DUP")
        _set_override(get_palet_bazli_stok_service, svc)

        resp = client.post(
            "/api/stok-islemleri/palet-giris",
            json={"palet_no": "PLT-DUP"},
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["id"] == 77
        svc.son_hareketi_getir_palet_ile.assert_called_once_with("PLT-DUP")

    def test_integrity_ve_mevcut_hareket_yoksa_409(self, client, depocu_user):
        svc = MagicMock()
        svc.palet_giris.side_effect = _integrity_error()
        svc.son_hareketi_getir_palet_ile.return_value = None
        _set_override(get_palet_bazli_stok_service, svc)

        resp = client.post(
            "/api/stok-islemleri/palet-giris",
            json={"palet_no": "PLT-DUP"},
        )
        assert resp.status_code == 409

    def test_bos_palet_no_422(self, client, depocu_user):
        _set_override(get_palet_bazli_stok_service, MagicMock())
        resp = client.post("/api/stok-islemleri/palet-giris", json={"palet_no": "   "})
        assert resp.status_code == 422


# ─────────────────────────────────────────
# POST /api/stok-islemleri/palet-cikis
# ─────────────────────────────────────────

class TestPaletCikis:
    def test_happy_path_kismi_cikis(self, client, depocu_user):
        svc = MagicMock()
        svc.palet_cikis.return_value = _hareket_stub(
            hareket_tipi="cikis", miktar=30, siparis_no="SIP-1",
        )
        _set_override(get_palet_bazli_stok_service, svc)

        resp = client.post(
            "/api/stok-islemleri/palet-cikis",
            json={
                "palet_no": "PLT-300",
                "miktar": 30,
                "siparis_no": "SIP-1",
                "aciklama": "Kısmi sevkiyat",
            },
        )

        assert resp.status_code == 201, resp.text
        # Service doğru parametrelerle çağrıldı
        call_kwargs = svc.palet_cikis.call_args.kwargs
        assert call_kwargs["palet_no"] == "PLT-300"
        assert call_kwargs["miktar"] == 30
        assert call_kwargs["siparis_no"] == "SIP-1"
        assert call_kwargs["aciklama"] == "Kısmi sevkiyat"

    def test_tam_cikis_miktar_none(self, client, depocu_user):
        svc = MagicMock()
        svc.palet_cikis.return_value = _hareket_stub(hareket_tipi="cikis", miktar=100)
        _set_override(get_palet_bazli_stok_service, svc)

        resp = client.post(
            "/api/stok-islemleri/palet-cikis",
            json={"palet_no": "PLT-300"},
        )
        assert resp.status_code == 201
        assert svc.palet_cikis.call_args.kwargs["miktar"] is None

    def test_negatif_miktar_422(self, client, depocu_user):
        _set_override(get_palet_bazli_stok_service, MagicMock())
        resp = client.post(
            "/api/stok-islemleri/palet-cikis",
            json={"palet_no": "PLT-300", "miktar": -5},
        )
        assert resp.status_code == 422

    def test_yetersiz_stok_400(self, client, depocu_user):
        svc = MagicMock()
        svc.palet_cikis.side_effect = YetersizStokError("Süt 1L", mevcut=10, istenen=30)
        _set_override(get_palet_bazli_stok_service, svc)

        resp = client.post(
            "/api/stok-islemleri/palet-cikis",
            json={"palet_no": "PLT-300", "miktar": 30},
        )
        assert resp.status_code == 400
        assert "stok" in resp.json()["error"].lower()

    def test_integrity_error_409(self, client, depocu_user):
        svc = MagicMock()
        svc.palet_cikis.side_effect = _integrity_error()
        _set_override(get_palet_bazli_stok_service, svc)

        resp = client.post(
            "/api/stok-islemleri/palet-cikis",
            json={"palet_no": "PLT-300"},
        )
        assert resp.status_code == 409


# ─────────────────────────────────────────
# POST /api/stok-islemleri/toplu-giris
# ─────────────────────────────────────────

class TestTopluGiris:
    def _sonuc(self, palet_no: str, basarili: bool, hareket_id: int | None = None, hata: str | None = None):
        return SimpleNamespace(
            palet_no=palet_no, basarili=basarili, hata_mesaji=hata,
            hareket=SimpleNamespace(id=hareket_id) if hareket_id else None,
        )

    def test_happy_path_commit_ve_kaynak_onay(self, client, depocu_user):
        svc = MagicMock()
        svc.toplu_palet_giris.return_value = [
            self._sonuc("PLT-1", True, 101),
            self._sonuc("PLT-2", True, 102),
        ]
        _set_override(get_palet_bazli_stok_service, svc)

        resp = client.post(
            "/api/stok-islemleri/toplu-giris",
            json={"palet_no_listesi": ["PLT-1", "PLT-2"], "irsaliye_no": "IRS-1"},
        )

        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["toplam"] == 2
        assert data["basarili"] == 2
        assert data["basarisiz"] == 0
        # Kaynak onayı commit sonrası çağrıldı
        svc.toplu_palet_giris_kaynagini_onayla.assert_called_once_with(["PLT-1", "PLT-2"])

    def test_pre_validation_fail_rollback_ve_kaynak_onay_yok(self, client, depocu_user):
        svc = MagicMock()
        svc.toplu_palet_giris.return_value = [
            self._sonuc("PLT-1", True, 101),
            self._sonuc("PLT-2", False, hata="Palet zaten kayıtlı"),
        ]
        _set_override(get_palet_bazli_stok_service, svc)

        resp = client.post(
            "/api/stok-islemleri/toplu-giris",
            json={"palet_no_listesi": ["PLT-1", "PLT-2"]},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["basarili"] == 1
        assert data["basarisiz"] == 1
        # Pre-validation fail → kaynak onayı atlanır
        svc.toplu_palet_giris_kaynagini_onayla.assert_not_called()

    def test_tekrarli_palet_no_422(self, client, depocu_user):
        _set_override(get_palet_bazli_stok_service, MagicMock())
        resp = client.post(
            "/api/stok-islemleri/toplu-giris",
            json={"palet_no_listesi": ["PLT-1", "PLT-1"]},
        )
        assert resp.status_code == 422

    def test_bos_liste_422(self, client, depocu_user):
        _set_override(get_palet_bazli_stok_service, MagicMock())
        resp = client.post(
            "/api/stok-islemleri/toplu-giris",
            json={"palet_no_listesi": []},
        )
        assert resp.status_code == 422

    def test_max_palet_asilirsa_422(self, client, depocu_user):
        _set_override(get_palet_bazli_stok_service, MagicMock())
        resp = client.post(
            "/api/stok-islemleri/toplu-giris",
            json={"palet_no_listesi": [f"P-{i}" for i in range(51)]},
        )
        assert resp.status_code == 422


# ─────────────────────────────────────────
# POST /api/stok-islemleri/toplu-cikis
# ─────────────────────────────────────────

class TestTopluCikis:
    def _sonuc(self, palet_no, basarili, hareket_id=None, hata=None):
        return SimpleNamespace(
            palet_no=palet_no, basarili=basarili, hata_mesaji=hata,
            hareket=SimpleNamespace(id=hareket_id) if hareket_id else None,
        )

    def test_happy_path_tum_meta_alanlari_iletilir(self, client, depocu_user):
        svc = MagicMock()
        svc.toplu_palet_cikis.return_value = [self._sonuc("PLT-1", True, 200)]
        _set_override(get_palet_bazli_stok_service, svc)

        body = {
            "kalemler": [{"palet_no": "PLT-1", "miktar": 50}],
            "siparis_no": "SIP-1",
            "tir_plaka": "34ABC",
            "depo_kapi": "KAPI-3",
            "sofor_adi": "Ali",
            "tasiyici_firma": "Demo Lojistik",
            "aciklama": "Sevkiyat",
        }
        resp = client.post("/api/stok-islemleri/toplu-cikis", json=body)

        assert resp.status_code == 200, resp.text
        call_kwargs = svc.toplu_palet_cikis.call_args.kwargs
        # Tüm sevkiyat metadatası doğru iletildi
        assert call_kwargs["siparis_no"] == "SIP-1"
        assert call_kwargs["tir_plaka"] == "34ABC"
        assert call_kwargs["depo_kapi"] == "KAPI-3"
        assert call_kwargs["sofor_adi"] == "Ali"
        assert call_kwargs["tasiyici_firma"] == "Demo Lojistik"
        assert call_kwargs["kalemler"] == [{"palet_no": "PLT-1", "miktar": 50}]

    def test_pre_validation_fail(self, client, depocu_user):
        svc = MagicMock()
        svc.toplu_palet_cikis.return_value = [
            self._sonuc("PLT-1", True, 200),
            self._sonuc("PLT-2", False, hata="Yetersiz stok"),
        ]
        _set_override(get_palet_bazli_stok_service, svc)

        resp = client.post(
            "/api/stok-islemleri/toplu-cikis",
            json={"kalemler": [{"palet_no": "PLT-1"}, {"palet_no": "PLT-2"}]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["basarisiz"] == 1
        # Sonuçlar DTO'ya doğru map'lendi
        hatali = next(s for s in data["sonuclar"] if s["palet_no"] == "PLT-2")
        assert hatali["basarili"] is False
        assert hatali["hata_mesaji"] == "Yetersiz stok"

    def test_integrity_error_commit_sirasinda_409(self, client, depocu_user):
        svc = MagicMock()
        svc.toplu_palet_cikis.return_value = [self._sonuc("PLT-1", True, 200)]
        _set_override(get_palet_bazli_stok_service, svc)

        # db.commit() IntegrityError fırlatsın
        class FakeDb:
            def commit(self_):
                raise _integrity_error()
            def rollback(self_):
                pass

        from database import get_db
        app.dependency_overrides[get_db] = lambda: FakeDb()

        resp = client.post(
            "/api/stok-islemleri/toplu-cikis",
            json={"kalemler": [{"palet_no": "PLT-1"}]},
        )
        assert resp.status_code == 409

    def test_negatif_miktar_422(self, client, depocu_user):
        _set_override(get_palet_bazli_stok_service, MagicMock())
        resp = client.post(
            "/api/stok-islemleri/toplu-cikis",
            json={"kalemler": [{"palet_no": "PLT-1", "miktar": -1}]},
        )
        assert resp.status_code == 422
