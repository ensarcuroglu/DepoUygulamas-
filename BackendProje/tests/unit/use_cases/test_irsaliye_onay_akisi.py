"""
Unit testler: IrsaliyeOnaylaVeGorevOlusturUseCase — irsaliye onay atomikliği.

Kapsam:
- TASLAK dışı irsaliye onaylanamaz
- Kalemsiz irsaliye onaylanamaz
- Staging rafı yoksa hata
- Her kalem için: Lot → Palet → StokHareketi → YerlestirmeGorevi oluşturulur
- Algoritma öneri veremezse palet staging rafa atanır ve görev gene oluşturulur
- İrsaliye ONAYLANDI durumuna geçer
- Tamamı tek çağrıda transaction'a yazılır (auto_commit=False palet için)
"""

import pytest
from unittest.mock import MagicMock, call, patch
from datetime import datetime, date

from app.application.use_cases.mal_kabul_irsaliye_use_cases import IrsaliyeOnaylaVeGorevOlusturUseCase
from app.core.entities.mal_kabul_irsaliye import MalKabulIrsaliye, MalKabulKalemi, MalKabulDurum
from app.core.entities.lot import Lot
from app.core.entities.palet import Palet
from app.core.entities.raf import Raf
from app.core.entities.urun import Urun
from app.core.entities.yerlestirme_gorevi import GorevDurum
from app.core.exceptions import GecersizIslemError

pytestmark = pytest.mark.unit


# ─── Yardımcılar ──────────────────────────────────────────────────────────

def _staging_raf() -> Raf:
    return Raf(id=999, kod="STG-000", kapasite=1000, zon_id=None, aktif=True)


def _kalem(palet_no="PLT-001", urun_id=1, miktar=10) -> MalKabulKalemi:
    return MalKabulKalemi(
        palet_no=palet_no,
        urun_id=urun_id,
        lot_no="L001",
        miktar=miktar,
        raf_id=None,
        uretim_tarihi=date(2026, 1, 1),
        son_kullanma_tarihi=date(2027, 1, 1),
    )


def _irsaliye(durum=MalKabulDurum.TASLAK, kalem_sayisi=1) -> MalKabulIrsaliye:
    kalemler = [_kalem(palet_no=f"PLT-{i:03d}", urun_id=1) for i in range(kalem_sayisi)]
    return MalKabulIrsaliye(
        id=1,
        irsaliye_no="MK-2026-001",
        tedarikci_id=1,
        depo_id=1,
        tarih=datetime(2026, 1, 1),
        durum=durum,
        kalemler=kalemler,
    )


def _use_case(irsaliye=None, staging_raf=None, algoritma_oneri=None):
    repo = MagicMock()
    urun_repo = MagicMock()
    lot_repo = MagicMock()
    palet_repo = MagicMock()
    hareket_repo = MagicMock()
    gorev_repo = MagicMock()
    raf_repo = MagicMock()
    algoritma = MagicMock()
    log_repo = MagicMock()
    db = MagicMock()

    # Varsayılan irsaliye
    repo.getir_id_ile.return_value = irsaliye or _irsaliye()
    # Staging raf
    raf_repo.getir_staging_raf.return_value = staging_raf if staging_raf is not None else _staging_raf()
    # Ürün doğrulama
    urun_repo.getir_id_ile.return_value = Urun(id=1, isim="Test Ürün", depolama_tipi="Kuru")
    # Lot — önce mevcut yok, sonra oluşturuldu
    lot_repo.getir_lot_no_ile.return_value = None
    lot_repo.olustur.return_value = Lot(id=10, urun_id=1, lot_no="L001", aktif=True)
    # Palet
    palet_repo.olustur.return_value = Palet(id=20, lot_id=10, raf_id=999, palet_no="PLT-001",
                                             koli_adedi=10, aktif=True)
    # Algoritma
    if algoritma_oneri is None:
        oneri_mock = MagicMock()
        oneri_mock.onerilen_raf = Raf(id=5, kod="GNL-A-01-01-01", kapasite=10, zon_id=1, aktif=True)
        algoritma.raf_oner.return_value = oneri_mock
    else:
        algoritma.raf_oner.return_value = algoritma_oneri

    uc = IrsaliyeOnaylaVeGorevOlusturUseCase(
        repo=repo,
        urun_repo=urun_repo,
        lot_repo=lot_repo,
        palet_repo=palet_repo,
        hareket_repo=hareket_repo,
        gorev_repo=gorev_repo,
        raf_repo=raf_repo,
        yerlestirme_algoritmasi=algoritma,
        log_repo=log_repo,
        db=db,
    )
    return uc, {
        "repo": repo, "urun_repo": urun_repo, "lot_repo": lot_repo,
        "palet_repo": palet_repo, "hareket_repo": hareket_repo,
        "gorev_repo": gorev_repo, "raf_repo": raf_repo,
        "algoritma": algoritma, "log_repo": log_repo, "db": db,
    }


# ─── Ön koşul hataları ────────────────────────────────────────────────────

class TestOnKosulHatalari:
    def test_taslak_olmayan_irsaliye_onaylanamaz(self):
        onaylanmis = _irsaliye(durum=MalKabulDurum.ONAYLANDI, kalem_sayisi=1)
        uc, _ = _use_case(irsaliye=onaylanmis)

        with pytest.raises(GecersizIslemError, match="taslak"):
            uc.execute(irsaliye_id=1, kullanici_id=1)

    def test_kalemsiz_irsaliye_onaylanamaz(self):
        bos_irsaliye = MalKabulIrsaliye(
            id=1, irsaliye_no="MK-BOŞ", tedarikci_id=1, depo_id=1,
            tarih=datetime(2026, 1, 1), durum=MalKabulDurum.TASLAK, kalemler=[],
        )
        uc, _ = _use_case(irsaliye=bos_irsaliye)

        with pytest.raises(GecersizIslemError, match="Kalemsiz"):
            uc.execute(irsaliye_id=1, kullanici_id=1)

    def test_staging_raf_yoksa_hata(self):
        uc, _ = _use_case(staging_raf=False)  # False → None döner

        with pytest.raises(GecersizIslemError, match="MIGRATION_STAGING"):
            uc.execute(irsaliye_id=1, kullanici_id=1)


# ─── Başarılı onay akışı ──────────────────────────────────────────────────

class TestBasariliOnayAkisi:
    def test_her_kalem_icin_palet_olusturulur(self):
        irsaliye = _irsaliye(kalem_sayisi=3)
        uc, m = _use_case(irsaliye=irsaliye)

        # Her kalem farklı lot numarası
        for i, kalem in enumerate(irsaliye.kalemler):
            kalem.lot_no = f"L{i:03d}"

        m["lot_repo"].olustur.return_value = Lot(id=10, urun_id=1, lot_no="L000", aktif=True)
        m["palet_repo"].olustur.return_value = Palet(id=20, lot_id=10, raf_id=999,
                                                       palet_no="PLT-000", koli_adedi=5, aktif=True)

        uc.execute(irsaliye_id=1, kullanici_id=1)

        assert m["palet_repo"].olustur.call_count == 3

    def test_her_kalem_icin_gorev_olusturulur(self):
        irsaliye = _irsaliye(kalem_sayisi=2)
        uc, m = _use_case(irsaliye=irsaliye)

        m["lot_repo"].olustur.return_value = Lot(id=10, urun_id=1, lot_no="L000", aktif=True)
        m["palet_repo"].olustur.return_value = Palet(id=20, lot_id=10, raf_id=999,
                                                       palet_no="PLT-000", koli_adedi=5, aktif=True)

        uc.execute(irsaliye_id=1, kullanici_id=1)

        assert m["gorev_repo"].olustur.call_count == 2

    def test_her_kalem_icin_stok_hareketi_olusturulur(self):
        irsaliye = _irsaliye(kalem_sayisi=2)
        uc, m = _use_case(irsaliye=irsaliye)

        m["lot_repo"].olustur.return_value = Lot(id=10, urun_id=1, lot_no="L000", aktif=True)
        m["palet_repo"].olustur.return_value = Palet(id=20, lot_id=10, raf_id=999,
                                                       palet_no="PLT-000", koli_adedi=5, aktif=True)

        uc.execute(irsaliye_id=1, kullanici_id=1)

        assert m["hareket_repo"].olustur.call_count == 2

    def test_algoritma_onerisi_gorev_onerilen_raf_id_olur(self):
        irsaliye = _irsaliye(kalem_sayisi=1)
        oneri = MagicMock()
        oneri.onerilen_raf = Raf(id=77, kod="GNL-B-02-01-01", kapasite=10, zon_id=1, aktif=True)

        uc, m = _use_case(irsaliye=irsaliye, algoritma_oneri=oneri)

        m["lot_repo"].olustur.return_value = Lot(id=10, urun_id=1, lot_no="L000", aktif=True)
        m["palet_repo"].olustur.return_value = Palet(id=20, lot_id=10, raf_id=999,
                                                       palet_no="PLT-000", koli_adedi=5, aktif=True)

        uc.execute(irsaliye_id=1, kullanici_id=1)

        gorev_cagri = m["gorev_repo"].olustur.call_args[0][0]
        assert gorev_cagri.onerilen_raf_id == 77

    def test_algoritma_oneri_veremezse_staging_raf_kullanilir(self):
        """Algoritma None döndürürse görev staging rafa atanır."""
        irsaliye = _irsaliye(kalem_sayisi=1)
        uc, m = _use_case(irsaliye=irsaliye, algoritma_oneri=None)
        m["algoritma"].raf_oner.return_value = None  # Uygun raf yok

        m["lot_repo"].olustur.return_value = Lot(id=10, urun_id=1, lot_no="L000", aktif=True)
        m["palet_repo"].olustur.return_value = Palet(id=20, lot_id=10, raf_id=999,
                                                       palet_no="PLT-000", koli_adedi=5, aktif=True)

        uc.execute(irsaliye_id=1, kullanici_id=1)

        gorev_cagri = m["gorev_repo"].olustur.call_args[0][0]
        # Staging rafı id=999
        assert gorev_cagri.onerilen_raf_id == 999

    def test_palet_auto_commit_false_ile_olusturulur(self):
        """Palet, transaction kapsamında yazılmalı (auto_commit=False)."""
        irsaliye = _irsaliye(kalem_sayisi=1)
        uc, m = _use_case(irsaliye=irsaliye)

        m["lot_repo"].olustur.return_value = Lot(id=10, urun_id=1, lot_no="L000", aktif=True)
        m["palet_repo"].olustur.return_value = Palet(id=20, lot_id=10, raf_id=999,
                                                       palet_no="PLT-000", koli_adedi=5, aktif=True)

        uc.execute(irsaliye_id=1, kullanici_id=1)

        _, kwargs = m["palet_repo"].olustur.call_args
        assert kwargs.get("auto_commit") is False

    def test_irsaliye_onaylandi_durumuna_gecer(self):
        irsaliye = _irsaliye(kalem_sayisi=1)
        uc, m = _use_case(irsaliye=irsaliye)

        m["lot_repo"].olustur.return_value = Lot(id=10, urun_id=1, lot_no="L000", aktif=True)
        m["palet_repo"].olustur.return_value = Palet(id=20, lot_id=10, raf_id=999,
                                                       palet_no="PLT-000", koli_adedi=5, aktif=True)
        m["repo"].guncelle.return_value = irsaliye

        uc.execute(irsaliye_id=1, kullanici_id=1)

        assert irsaliye.durum == MalKabulDurum.ONAYLANDI

    def test_mevcut_lot_yeniden_kullanilir(self):
        """Aynı lot_no için yeni lot oluşturulmaz, mevcutu kullanılır."""
        irsaliye = _irsaliye(kalem_sayisi=1)
        mevcut_lot = Lot(id=5, urun_id=1, lot_no="L001", aktif=True)

        uc, m = _use_case(irsaliye=irsaliye)
        m["lot_repo"].getir_lot_no_ile.return_value = mevcut_lot
        m["palet_repo"].olustur.return_value = Palet(id=20, lot_id=5, raf_id=999,
                                                       palet_no="PLT-000", koli_adedi=5, aktif=True)

        uc.execute(irsaliye_id=1, kullanici_id=1)

        m["lot_repo"].olustur.assert_not_called()

    def test_sistem_log_yazilir(self):
        irsaliye = _irsaliye(kalem_sayisi=1)
        uc, m = _use_case(irsaliye=irsaliye)

        m["lot_repo"].olustur.return_value = Lot(id=10, urun_id=1, lot_no="L000", aktif=True)
        m["palet_repo"].olustur.return_value = Palet(id=20, lot_id=10, raf_id=999,
                                                       palet_no="PLT-000", koli_adedi=5, aktif=True)

        uc.execute(irsaliye_id=1, kullanici_id=1)

        assert m["log_repo"].olustur.call_count >= 1
