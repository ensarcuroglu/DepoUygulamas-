"""Unit testler: app.application.use_cases.mal_kabul_irsaliye_use_cases.

Kapsam: listele/getir/oluştur/güncelle/sil/istisna + inbound dashboard.
İrsaliye onaylama akışı zaten `test_irsaliye_onay_akisi.py` içinde test ediliyor;
burada CRUD + durum geçişi + istisna bildirimi davranışı doğrulanır.
"""

from __future__ import annotations

from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from app.application.dto.mal_kabul_irsaliye_dto import (
    MalKabulIrsaliyeGuncelleRequestDTO,
    MalKabulIrsaliyeOlusturRequestDTO,
    MalKabulKalemiIstisnaRequestDTO,
    MalKabulKalemiOlusturDTO,
)
from app.application.use_cases.mal_kabul_irsaliye_use_cases import (
    InboundDashboardUseCase,
    MalKabulIrsaliyeGetirUseCase,
    MalKabulIrsaliyeGuncelleUseCase,
    MalKabulIrsaliyeListeleUseCase,
    MalKabulIrsaliyeOlusturUseCase,
    MalKabulIrsaliyeSilUseCase,
    MalKabulKalemiIstisnaBildirUseCase,
)
from app.core.entities.mal_kabul_irsaliye import (
    IstisnaKalemTip,
    MalKabulDurum,
    MalKabulIrsaliye,
    MalKabulKalemi,
)
from app.core.exceptions import (
    GecersizDurumGecisiError,
    GecersizIslemError,
    KayitBulunamadiError,
)

pytestmark = pytest.mark.unit


def _kalem_dto(**over) -> MalKabulKalemiOlusturDTO:
    return MalKabulKalemiOlusturDTO(
        palet_no=over.get("palet_no", "PLT-001"),
        urun_id=over.get("urun_id", 1),
        lot_no=over.get("lot_no", "L-1"),
        miktar=over.get("miktar", 10),
        uretim_tarihi=over.get("uretim_tarihi"),
        son_kullanma_tarihi=over.get("son_kullanma_tarihi"),
    )


def _olustur_dto(kalemler=None) -> MalKabulIrsaliyeOlusturRequestDTO:
    return MalKabulIrsaliyeOlusturRequestDTO(
        tedarikci_id=1,
        depo_id=1,
        tarih=date(2026, 4, 20),
        tir_plaka="34ABC123",
        sofor_adi="Ali",
        kalemler=kalemler if kalemler is not None else [_kalem_dto()],
    )


def _irsaliye(
    *,
    id: int = 1,
    durum: str = MalKabulDurum.TASLAK,
    kalemler: list[MalKabulKalemi] | None = None,
) -> MalKabulIrsaliye:
    return MalKabulIrsaliye(
        id=id,
        irsaliye_no="IRS-001",
        tedarikci_id=1,
        depo_id=1,
        tarih=date(2026, 4, 20),
        durum=durum,
        kalemler=kalemler if kalemler is not None else [
            MalKabulKalemi(id=1, mal_kabul_irsaliyesi_id=id, palet_no="P-1", urun_id=1, miktar=10),
        ],
    )


# ─────────────────────────────────────────────────────────────────
# LİSTELE / GETİR
# ─────────────────────────────────────────────────────────────────

class TestListeleGetir:
    def test_listele_filtreler_delege_edilir(self):
        repo = MagicMock()
        repo.getir_hepsi.return_value = [_irsaliye(id=1), _irsaliye(id=2)]
        uc = MalKabulIrsaliyeListeleUseCase(repo)

        sonuc = uc.execute(
            skip=5, limit=10, durum="Taslak",
            arama="IRS", depo_id=1, tedarikci_id=2,
        )
        assert len(sonuc) == 2
        repo.getir_hepsi.assert_called_once_with(
            skip=5, limit=10, durum="Taslak",
            arama="IRS", depo_id=1, tedarikci_id=2,
        )

    def test_getir_yoksa_hata(self):
        repo = MagicMock()
        repo.getir_id_ile.return_value = None
        with pytest.raises(KayitBulunamadiError):
            MalKabulIrsaliyeGetirUseCase(repo).execute(irsaliye_id=1)

    def test_getir_happy_path(self):
        repo = MagicMock()
        repo.getir_id_ile.return_value = _irsaliye(id=9)
        sonuc = MalKabulIrsaliyeGetirUseCase(repo).execute(irsaliye_id=9)
        assert sonuc.id == 9


# ─────────────────────────────────────────────────────────────────
# OLUŞTUR
# ─────────────────────────────────────────────────────────────────

class TestOlustur:
    def _mocks(self):
        return {
            "repo": MagicMock(),
            "tedarikci_repo": MagicMock(),
            "depo_repo": MagicMock(),
            "urun_repo": MagicMock(),
            "log_repo": MagicMock(),
        }

    def test_tedarikci_yoksa_hata(self):
        m = self._mocks()
        m["tedarikci_repo"].getir_id_ile.return_value = None
        uc = MalKabulIrsaliyeOlusturUseCase(**m)
        with pytest.raises(KayitBulunamadiError):
            uc.execute(_olustur_dto(), kullanici_id=5)
        m["repo"].olustur.assert_not_called()

    def test_depo_yoksa_hata(self):
        m = self._mocks()
        m["tedarikci_repo"].getir_id_ile.return_value = MagicMock()
        m["depo_repo"].getir_id_ile.return_value = None
        uc = MalKabulIrsaliyeOlusturUseCase(**m)
        with pytest.raises(KayitBulunamadiError):
            uc.execute(_olustur_dto(), kullanici_id=5)

    def test_urun_yoksa_hata(self):
        m = self._mocks()
        m["tedarikci_repo"].getir_id_ile.return_value = MagicMock()
        m["depo_repo"].getir_id_ile.return_value = MagicMock()
        m["urun_repo"].getir_id_ile.return_value = None
        uc = MalKabulIrsaliyeOlusturUseCase(**m)
        with pytest.raises(KayitBulunamadiError):
            uc.execute(_olustur_dto(), kullanici_id=5)

    def test_happy_path_irsaliye_no_cagrilir_ve_log_atar(self):
        m = self._mocks()
        m["tedarikci_repo"].getir_id_ile.return_value = MagicMock()
        m["depo_repo"].getir_id_ile.return_value = MagicMock()
        m["urun_repo"].getir_id_ile.return_value = MagicMock()
        m["repo"].sonraki_irsaliye_no.return_value = "IRS-001"

        def _olustur(entity):
            entity.id = 42
            for i, k in enumerate(entity.kalemler, start=1):
                k.id = i
                k.mal_kabul_irsaliyesi_id = 42
            return entity

        m["repo"].olustur.side_effect = _olustur

        uc = MalKabulIrsaliyeOlusturUseCase(**m)
        dto = _olustur_dto(kalemler=[_kalem_dto(palet_no="PLT-1"), _kalem_dto(palet_no="PLT-2")])

        sonuc = uc.execute(dto, kullanici_id=5)

        assert sonuc.id == 42
        assert sonuc.irsaliye_no == "IRS-001"
        assert len(sonuc.kalemler) == 2
        m["repo"].sonraki_irsaliye_no.assert_called_once()
        m["log_repo"].olustur.assert_called_once()


# ─────────────────────────────────────────────────────────────────
# GÜNCELLE
# ─────────────────────────────────────────────────────────────────

class TestGuncelle:
    def _mocks(self):
        return {
            "repo": MagicMock(),
            "urun_repo": MagicMock(),
            "log_repo": MagicMock(),
        }

    def test_yoksa_hata(self):
        m = self._mocks()
        m["repo"].getir_id_ile.return_value = None
        with pytest.raises(KayitBulunamadiError):
            MalKabulIrsaliyeGuncelleUseCase(**m).execute(
                1, MalKabulIrsaliyeGuncelleRequestDTO(), kullanici_id=5,
            )

    def test_taslak_alan_guncelleme_calisir(self):
        m = self._mocks()
        irsaliye = _irsaliye(durum=MalKabulDurum.TASLAK)
        m["repo"].getir_id_ile.return_value = irsaliye
        m["repo"].guncelle.return_value = irsaliye

        dto = MalKabulIrsaliyeGuncelleRequestDTO(tir_plaka="06TEST", sofor_adi="Veli")
        sonuc = MalKabulIrsaliyeGuncelleUseCase(**m).execute(1, dto, kullanici_id=5)

        assert irsaliye.tir_plaka == "06TEST"
        assert irsaliye.sofor_adi == "Veli"
        assert sonuc.tir_plaka == "06TEST"

    def test_onaylandi_irsaliye_temel_alan_guncellenemez(self):
        """Onaylandı durumunda sadece durum değişiyor, diğer alanlar yoksayılıyor."""
        m = self._mocks()
        irsaliye = _irsaliye(durum=MalKabulDurum.ONAYLANDI)
        irsaliye.tir_plaka = "34ORG"
        m["repo"].getir_id_ile.return_value = irsaliye
        m["repo"].guncelle.return_value = irsaliye

        dto = MalKabulIrsaliyeGuncelleRequestDTO(tir_plaka="34YENI")
        MalKabulIrsaliyeGuncelleUseCase(**m).execute(1, dto, kullanici_id=5)

        # Taslak olmadığı için tir_plaka güncellenmez
        assert irsaliye.tir_plaka == "34ORG"

    def test_onaylandi_durumuna_gecis_log_atar(self):
        m = self._mocks()
        irsaliye = _irsaliye(durum=MalKabulDurum.TASLAK)
        m["repo"].getir_id_ile.return_value = irsaliye
        m["repo"].guncelle.return_value = irsaliye

        dto = MalKabulIrsaliyeGuncelleRequestDTO(durum=MalKabulDurum.ONAYLANDI)
        MalKabulIrsaliyeGuncelleUseCase(**m).execute(1, dto, kullanici_id=5)

        assert irsaliye.durum == MalKabulDurum.ONAYLANDI
        m["log_repo"].olustur.assert_called_once()

    def test_gecersiz_durum_gecisi_hata(self):
        """Kapandı irsaliyeye tekrar durum set edilemez."""
        m = self._mocks()
        m["repo"].getir_id_ile.return_value = _irsaliye(durum=MalKabulDurum.KAPANDI)

        dto = MalKabulIrsaliyeGuncelleRequestDTO(durum=MalKabulDurum.ONAYLANDI)
        with pytest.raises(GecersizDurumGecisiError):
            MalKabulIrsaliyeGuncelleUseCase(**m).execute(1, dto, kullanici_id=5)

    def test_kalem_guncelleme_urun_dogrular(self):
        m = self._mocks()
        irsaliye = _irsaliye(durum=MalKabulDurum.TASLAK)
        m["repo"].getir_id_ile.return_value = irsaliye
        m["repo"].guncelle.return_value = irsaliye
        m["urun_repo"].getir_id_ile.return_value = None  # ürün yok

        dto = MalKabulIrsaliyeGuncelleRequestDTO(kalemler=[_kalem_dto(urun_id=999)])
        with pytest.raises(KayitBulunamadiError):
            MalKabulIrsaliyeGuncelleUseCase(**m).execute(1, dto, kullanici_id=5)


# ─────────────────────────────────────────────────────────────────
# SİL
# ─────────────────────────────────────────────────────────────────

class TestSil:
    def test_yoksa_hata(self):
        repo = MagicMock(); log = MagicMock()
        repo.getir_id_ile.return_value = None
        with pytest.raises(KayitBulunamadiError):
            MalKabulIrsaliyeSilUseCase(repo, log).execute(irsaliye_id=1, kullanici_id=5)

    def test_onaylandi_silinemez(self):
        repo = MagicMock(); log = MagicMock()
        repo.getir_id_ile.return_value = _irsaliye(durum=MalKabulDurum.ONAYLANDI)
        with pytest.raises(GecersizIslemError, match="taslak"):
            MalKabulIrsaliyeSilUseCase(repo, log).execute(irsaliye_id=1, kullanici_id=5)

    def test_taslak_silinir_ve_log_atar(self):
        repo = MagicMock(); log = MagicMock()
        repo.getir_id_ile.return_value = _irsaliye(durum=MalKabulDurum.TASLAK)
        repo.sil.return_value = True

        sonuc = MalKabulIrsaliyeSilUseCase(repo, log).execute(irsaliye_id=1, kullanici_id=5)

        assert sonuc is True
        repo.sil.assert_called_once_with(1)
        log.olustur.assert_called_once()


# ─────────────────────────────────────────────────────────────────
# İSTİSNA BİLDİR
# ─────────────────────────────────────────────────────────────────

class TestKalemIstisnaBildir:
    def _dto(self, tip=IstisnaKalemTip.EKSIK, miktar=8):
        return MalKabulKalemiIstisnaRequestDTO(
            istisna_tip=tip,
            istisna_aciklama="Fiziksel sayımda eksik",
            gerceklesen_miktar=miktar,
        )

    def test_irsaliye_yoksa_hata(self):
        repo = MagicMock(); log = MagicMock()
        repo.getir_id_ile.return_value = None
        with pytest.raises(KayitBulunamadiError):
            MalKabulKalemiIstisnaBildirUseCase(repo, log).execute(
                irsaliye_id=1, kalem_id=1, dto=self._dto(), kullanici_id=5,
            )

    def test_kapanmis_irsaliye_istisna_alamaz(self):
        repo = MagicMock(); log = MagicMock()
        repo.getir_id_ile.return_value = _irsaliye(durum=MalKabulDurum.KAPANDI)
        with pytest.raises(GecersizIslemError, match="Kapan"):
            MalKabulKalemiIstisnaBildirUseCase(repo, log).execute(
                irsaliye_id=1, kalem_id=1, dto=self._dto(), kullanici_id=5,
            )

    def test_kalem_yoksa_hata(self):
        repo = MagicMock(); log = MagicMock()
        repo.getir_id_ile.return_value = _irsaliye(
            durum=MalKabulDurum.ONAYLANDI,
            kalemler=[MalKabulKalemi(id=1, mal_kabul_irsaliyesi_id=1, palet_no="P-1", urun_id=1, miktar=10)],
        )
        with pytest.raises(KayitBulunamadiError):
            MalKabulKalemiIstisnaBildirUseCase(repo, log).execute(
                irsaliye_id=1, kalem_id=99, dto=self._dto(), kullanici_id=5,
            )

    def test_happy_path_istisna_kaydeder(self):
        repo = MagicMock(); log = MagicMock()
        kalem = MalKabulKalemi(id=5, mal_kabul_irsaliyesi_id=1, palet_no="P-1", urun_id=1, miktar=10)
        irsaliye = _irsaliye(durum=MalKabulDurum.ONAYLANDI, kalemler=[kalem])
        # getir_id_ile iki kez: bir kontrol, bir response için
        repo.getir_id_ile.return_value = irsaliye

        dto = self._dto(tip=IstisnaKalemTip.HASARLI, miktar=6)
        sonuc = MalKabulKalemiIstisnaBildirUseCase(repo, log).execute(
            irsaliye_id=1, kalem_id=5, dto=dto, kullanici_id=5,
        )

        assert kalem.istisna_tip == IstisnaKalemTip.HASARLI
        assert kalem.gerceklesen_miktar == 6
        repo.kalem_guncelle.assert_called_once()
        log.olustur.assert_called_once()
        assert sonuc.istisna_sayisi >= 1


# ─────────────────────────────────────────────────────────────────
# INBOUND DASHBOARD
# ─────────────────────────────────────────────────────────────────

class TestInboundDashboard:
    def test_repo_verisini_dto_olarak_doner(self):
        repo = MagicMock()
        repo.inbound_dashboard_istatistik.return_value = {
            "irsaliye_toplam": 10,
            "irsaliye_taslak": 3,
            "irsaliye_onaylandi": 5,
            "irsaliye_kapandi": 2,
            "gorev_toplam": 20,
            "gorev_bekleyen": 4,
            "gorev_devam_eden": 3,
            "gorev_tamamlanan": 11,
            "gorev_iptal": 2,
            "ort_yerlestirme_sure_dk": 12.5,
            "istisna_sayisi": 1,
            "override_sayisi": 0,
            "bugunun_irsaliyeleri": [
                {
                    "id": 1,
                    "irsaliye_no": "IRS-001",
                    "tedarikci_adi": "Demo",
                    "durum": MalKabulDurum.ONAYLANDI,
                    "kalem_sayisi": 2,
                    "yerlestirilen": 1,
                    "bekleyen": 1,
                    "tarih": date(2026, 4, 20),
                }
            ],
        }

        sonuc = InboundDashboardUseCase(repo).execute()

        assert sonuc.irsaliye_toplam == 10
        assert sonuc.gorev_tamamlanan == 11
        assert sonuc.ort_yerlestirme_sure_dk == 12.5
        assert len(sonuc.bugunun_irsaliyeleri) == 1
        assert sonuc.bugunun_irsaliyeleri[0].irsaliye_no == "IRS-001"
