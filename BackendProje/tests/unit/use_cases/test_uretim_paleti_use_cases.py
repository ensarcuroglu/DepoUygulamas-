"""Unit testleri — Üretim Paleti use case'leri.

Tüm bağımlılıklar mock'lanır; transaction sınırı ve yetki enforcement test edilir.
"""

import pytest
from unittest.mock import MagicMock
from datetime import datetime

from app.core.entities.palet import Palet, UretimPaletDurum
from app.core.entities.kullanici import Kullanici, KullaniciRol
from app.core.entities.palet_durum_log import PaletDurumLog
from app.core.entities.stok_hareketi import HareketTipi
from app.core.exceptions import GecersizIslemError, KayitBulunamadiError, YetkisizIslemError
from app.core.services.uretim_palet_service import UretimPaletService
from app.application.use_cases.uretim_paleti_use_cases import (
    UretimPaletiOlusturUseCase,
    UretimPaletiKabulEtUseCase,
    UretimPaletiKarantinaAlUseCase,
    UretimPaletiKarantinaCikarUseCase,
    UretimPaletiIptalUseCase,
    UretimPaletleriListeleUseCase,
    UretimPaletiGetirUseCase,
)
from app.application.dto.uretim_paleti_dto import UretimPaletiOlusturRequestDTO


# ── Yardımcılar ───────────────────────────────────────────────────────────────

def _kullanici(rol: str = KullaniciRol.ADMIN) -> Kullanici:
    return Kullanici(id=1, kullanici_adi="test", rol=rol)


def _uretim_palet(durum: str = UretimPaletDurum.KABUL_BEKLIYOR) -> Palet:
    return Palet(
        id=10,
        palet_no="PRD-20250416-0001",
        lot_id=5,
        raf_id=0,
        koli_adedi=48,
        kaynak="uretim",
        durum=durum,
        aktif=True,
        olusturma_tarihi=datetime.utcnow(),
    )


def _mock_db():
    db = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()
    return db


def _mock_log() -> PaletDurumLog:
    return PaletDurumLog(palet_id=10, yeni_durum=UretimPaletDurum.KABUL_EDILDI)


# ── Listele/GetirUseCase ──────────────────────────────────────────────────────

class TestUretimPaletiListeleGetir:
    def test_liste_vardiya_filtresini_repo_seviyesine_tasir(self):
        palet_repo = MagicMock()
        palet_repo.getir_hepsi.return_value = [_uretim_palet()]
        uc = UretimPaletleriListeleUseCase(palet_repo=palet_repo)

        uc.execute(skip=10, limit=25, vardiya="A")

        palet_repo.getir_hepsi.assert_called_once_with(
            skip=10,
            limit=25,
            lot_id=None,
            sadece_aktif=True,
            kaynak="uretim",
            durum=None,
            vardiya="A",
        )

    def test_getir_uretim_kaynakli_olmayan_paleti_bulunamadi_sayar(self):
        legacy_palet = Palet(
            id=11,
            palet_no="PLT-LEGACY-001",
            lot_id=5,
            raf_id=1,
            koli_adedi=12,
            kaynak="irsaliye",
            durum=None,
            aktif=True,
        )
        palet_repo = MagicMock()
        palet_repo.getir_palet_no_ile.return_value = legacy_palet
        uc = UretimPaletiGetirUseCase(palet_repo=palet_repo)

        with pytest.raises(KayitBulunamadiError):
            uc.execute("PLT-LEGACY-001")


# ── OlusturUseCase ────────────────────────────────────────────────────────────

class TestUretimPaletiOlustur:
    def _make_uc(self, palet_no="PRD-20250416-0001"):
        domain_svc = UretimPaletService()
        seri_uretici = MagicMock()
        seri_uretici.uret.return_value = palet_no

        lot_repo = MagicMock()
        lot_repo.getir_id_ile.return_value = MagicMock(id=5, urun_id=3)

        raf_repo = MagicMock()
        raf_repo.getir_staging_raf.return_value = MagicMock(id=77)

        palet_kaydedilen = _uretim_palet(UretimPaletDurum.OLUSTURULDU)
        palet_kaydedilen.raf_id = 77
        palet_repo = MagicMock()
        palet_repo.olustur.return_value = palet_kaydedilen

        durum_log_repo = MagicMock()
        log_repo = MagicMock()
        db = _mock_db()

        uc = UretimPaletiOlusturUseCase(
            domain_service=domain_svc,
            seri_no_uretici=seri_uretici,
            palet_repo=palet_repo,
            lot_repo=lot_repo,
            raf_repo=raf_repo,
            durum_log_repo=durum_log_repo,
            sistem_log_repo=log_repo,
            db=db,
        )
        return uc, {"seri": seri_uretici, "palet_repo": palet_repo,
                    "lot_repo": lot_repo, "durum_log_repo": durum_log_repo,
                    "log_repo": log_repo, "db": db, "raf_repo": raf_repo}

    def test_lot_bulunamazsa_hata(self):
        uc, m = self._make_uc()
        m["lot_repo"].getir_id_ile.return_value = None
        dto = UretimPaletiOlusturRequestDTO(lot_id=99, koli_adedi=10)
        with pytest.raises(KayitBulunamadiError):
            uc.execute(dto, _kullanici())

    def test_palet_ve_durum_log_persist_edilir(self):
        uc, m = self._make_uc()
        dto = UretimPaletiOlusturRequestDTO(lot_id=5, koli_adedi=48)
        kullanici = _kullanici()
        kullanici.depo_id = 3
        uc.execute(dto, kullanici)
        m["palet_repo"].olustur.assert_called_once()
        m["durum_log_repo"].olustur.assert_called_once()

    def test_db_commit_cagirilir(self):
        uc, m = self._make_uc()
        dto = UretimPaletiOlusturRequestDTO(lot_id=5, koli_adedi=48)
        kullanici = _kullanici()
        kullanici.depo_id = 3
        uc.execute(dto, kullanici)
        m["db"].commit.assert_called_once()

    def test_hata_durumunda_rollback(self):
        uc, m = self._make_uc()
        m["palet_repo"].olustur.side_effect = RuntimeError("DB error")
        dto = UretimPaletiOlusturRequestDTO(lot_id=5, koli_adedi=48)
        kullanici = _kullanici()
        kullanici.depo_id = 3
        with pytest.raises(RuntimeError):
            uc.execute(dto, kullanici)
        m["db"].rollback.assert_called_once()

    def test_staging_rafi_ve_cozumlenen_tarihi_entityye_yazar(self):
        uc, m = self._make_uc()
        dto = UretimPaletiOlusturRequestDTO(lot_id=5, koli_adedi=48)
        kullanici = _kullanici()
        kullanici.depo_id = 3

        uc.execute(dto, kullanici)

        palet_arg = m["palet_repo"].olustur.call_args[0][0]
        seri_tarihi = m["seri"].uret.call_args[0][0]
        assert palet_arg.raf_id == 77
        assert palet_arg.uretim_tarihi == seri_tarihi
        m["raf_repo"].getir_staging_raf.assert_called_once_with(3)

    def test_staging_rafi_bulunamazsa_hata(self):
        uc, m = self._make_uc()
        m["raf_repo"].getir_staging_raf.return_value = None
        dto = UretimPaletiOlusturRequestDTO(lot_id=5, koli_adedi=48)
        kullanici = _kullanici()
        kullanici.depo_id = 3

        with pytest.raises(GecersizIslemError, match="MIGRATION_STAGING"):
            uc.execute(dto, kullanici)

    def test_depo_baglamiyoksa_hata(self):
        uc, _ = self._make_uc()
        dto = UretimPaletiOlusturRequestDTO(lot_id=5, koli_adedi=48)

        with pytest.raises(GecersizIslemError, match="depo bağlamı"):
            uc.execute(dto, _kullanici())


# ── KabulEtUseCase ────────────────────────────────────────────────────────────

class TestUretimPaletiKabulEt:
    def _make_uc(self, palet: Palet):
        domain_svc = UretimPaletService()
        palet_repo = MagicMock()
        palet_repo.getir_palet_no_ile.return_value = palet
        palet_repo.guncelle.return_value = palet

        lot_mock = MagicMock(id=5, urun_id=3)
        lot_repo = MagicMock()
        lot_repo.getir_id_ile.return_value = lot_mock

        hareket_repo = MagicMock()
        hareket_repo.olustur.return_value = MagicMock()

        durum_log_repo = MagicMock()
        log_repo = MagicMock()
        db = _mock_db()

        uc = UretimPaletiKabulEtUseCase(
            domain_service=domain_svc,
            palet_repo=palet_repo,
            lot_repo=lot_repo,
            hareket_repo=hareket_repo,
            durum_log_repo=durum_log_repo,
            sistem_log_repo=log_repo,
            db=db,
        )
        return uc, {"palet_repo": palet_repo, "hareket_repo": hareket_repo,
                    "durum_log_repo": durum_log_repo, "db": db}

    def test_kabul_et_stok_hareketi_giris_yazar(self):
        """Kabul use case StokHareketi.GIRIS yazdığını doğrular."""
        palet = _uretim_palet(UretimPaletDurum.KABUL_BEKLIYOR)
        uc, m = self._make_uc(palet)
        uc.execute(palet.palet_no, _kullanici(KullaniciRol.DEPOCU))
        m["hareket_repo"].olustur.assert_called_once()
        hareket_arg = m["hareket_repo"].olustur.call_args[0][0]
        assert hareket_arg.hareket_tipi == HareketTipi.GIRIS

    def test_depocu_yetkisi_yeterli(self):
        palet = _uretim_palet(UretimPaletDurum.KABUL_BEKLIYOR)
        uc, _ = self._make_uc(palet)
        # exception fırlatmaz
        uc.execute(palet.palet_no, _kullanici(KullaniciRol.DEPOCU))

    def test_goruntuleyen_yetkisiz(self):
        palet = _uretim_palet(UretimPaletDurum.KABUL_BEKLIYOR)
        uc, _ = self._make_uc(palet)
        with pytest.raises(YetkisizIslemError):
            uc.execute(palet.palet_no, _kullanici(KullaniciRol.GORUNTULEYEN))

    def test_palet_bulunamazsa_hata(self):
        palet = _uretim_palet(UretimPaletDurum.KABUL_BEKLIYOR)
        uc, m = self._make_uc(palet)
        m["palet_repo"].getir_palet_no_ile.return_value = None
        with pytest.raises(KayitBulunamadiError):
            uc.execute("PRD-YANLISNO", _kullanici())


# ── KarantinaAlUseCase ────────────────────────────────────────────────────────

class TestUretimPaletiKarantinaAl:
    def _make_uc(self, palet: Palet):
        domain_svc = UretimPaletService()
        palet_repo = MagicMock()
        palet_repo.getir_palet_no_ile.return_value = palet
        palet_repo.guncelle.return_value = palet
        durum_log_repo = MagicMock()
        log_repo = MagicMock()
        db = _mock_db()
        uc = UretimPaletiKarantinaAlUseCase(
            domain_service=domain_svc,
            palet_repo=palet_repo,
            durum_log_repo=durum_log_repo,
            sistem_log_repo=log_repo,
            db=db,
        )
        return uc, {"db": db, "durum_log_repo": durum_log_repo}

    def test_kabul_edildi_den_karantina(self):
        palet = _uretim_palet(UretimPaletDurum.KABUL_EDILDI)
        uc, m = self._make_uc(palet)
        uc.execute(palet.palet_no, _kullanici(KullaniciRol.DEPOCU), sebep="Hasar")
        assert palet.durum == UretimPaletDurum.KARANTINA
        m["db"].commit.assert_called_once()

    def test_kalite_departmani_karantinaya_alabilir(self):
        palet = _uretim_palet(UretimPaletDurum.KABUL_EDILDI)
        uc, _ = self._make_uc(palet)
        kullanici = _kullanici(KullaniciRol.GORUNTULEYEN)
        kullanici.departman = "Kalite"

        uc.execute(palet.palet_no, kullanici, sebep="Hasar")

        assert palet.durum == UretimPaletDurum.KARANTINA


# ── KarantinaCikarUseCase ─────────────────────────────────────────────────────

class TestUretimPaletiKarantinaCikar:
    def _make_uc(self, palet: Palet):
        domain_svc = UretimPaletService()
        palet_repo = MagicMock()
        palet_repo.getir_palet_no_ile.return_value = palet
        palet_repo.guncelle.return_value = palet
        durum_log_repo = MagicMock()
        log_repo = MagicMock()
        db = _mock_db()
        uc = UretimPaletiKarantinaCikarUseCase(
            domain_service=domain_svc,
            palet_repo=palet_repo,
            durum_log_repo=durum_log_repo,
            sistem_log_repo=log_repo,
            db=db,
        )
        return uc

    def test_admin_karantinadan_cikarabilir(self):
        palet = _uretim_palet(UretimPaletDurum.KARANTINA)
        uc = self._make_uc(palet)
        uc.execute(palet.palet_no, _kullanici(KullaniciRol.ADMIN))
        assert palet.durum == UretimPaletDurum.KABUL_EDILDI

    def test_kalite_departmani_karantinadan_cikarabilir(self):
        palet = _uretim_palet(UretimPaletDurum.KARANTINA)
        uc = self._make_uc(palet)
        kullanici = _kullanici(KullaniciRol.GORUNTULEYEN)
        kullanici.departman = "kalite"

        uc.execute(palet.palet_no, kullanici)

        assert palet.durum == UretimPaletDurum.KABUL_EDILDI

    def test_depocu_karantinadan_cikaramaz(self):
        palet = _uretim_palet(UretimPaletDurum.KARANTINA)
        uc = self._make_uc(palet)
        with pytest.raises(YetkisizIslemError):
            uc.execute(palet.palet_no, _kullanici(KullaniciRol.DEPOCU))


# ── IptalUseCase ──────────────────────────────────────────────────────────────

class TestUretimPaletiIptal:
    def _make_uc(self, palet: Palet):
        domain_svc = UretimPaletService()
        palet_repo = MagicMock()
        palet_repo.getir_palet_no_ile.return_value = palet
        palet_repo.guncelle.return_value = palet
        durum_log_repo = MagicMock()
        log_repo = MagicMock()
        db = _mock_db()
        uc = UretimPaletiIptalUseCase(
            domain_service=domain_svc,
            palet_repo=palet_repo,
            durum_log_repo=durum_log_repo,
            sistem_log_repo=log_repo,
            db=db,
        )
        return uc, {"db": db}

    def test_admin_iptal_edebilir(self):
        palet = _uretim_palet(UretimPaletDurum.OLUSTURULDU)
        uc, m = self._make_uc(palet)
        uc.execute(palet.palet_no, _kullanici(KullaniciRol.ADMIN), sebep="Test")
        assert palet.durum == UretimPaletDurum.IPTAL_EDILDI
        m["db"].commit.assert_called_once()

    def test_depocu_iptal_edemez(self):
        palet = _uretim_palet(UretimPaletDurum.OLUSTURULDU)
        uc, _ = self._make_uc(palet)
        with pytest.raises(YetkisizIslemError):
            uc.execute(palet.palet_no, _kullanici(KullaniciRol.DEPOCU), sebep="Test")
