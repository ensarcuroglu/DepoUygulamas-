"""Unit testler: app.application.use_cases.yerlestirme_gorevi_use_cases.

Gerçek davranış testleri — repository/servis bağımlılıkları MagicMock ile izole.
Hedef: not found, yetki, geçersiz durum, override, karantina, staging senaryoları.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.application.dto.yerlestirme_gorevi_dto import (
    KarantinadanCikarRequestDTO,
    KarantinayaAlRequestDTO,
    YerlestirmeGoreviIptalRequestDTO,
    YerlestirmeGoreviOlusturRequestDTO,
    YerlestirmeGoreviOverrideRequestDTO,
    YerlestirmeGoreviTamamlaRequestDTO,
    YerlestirmeOnaylaRequestDTO,
)
from app.application.use_cases.yerlestirme_gorevi_use_cases import (
    BilinmeyenKonumGorevleriOlusturUseCase,
    KarantinadanCikarUseCase,
    KarantinayaAlUseCase,
    SonrakiGorevisiniAlUseCase,
    YerlestirmeGoreviBaslatUseCase,
    YerlestirmeGoreviBirakUseCase,
    YerlestirmeGoreviGetirUseCase,
    YerlestirmeGoreviIptalUseCase,
    YerlestirmeGoreviListeleUseCase,
    YerlestirmeGoreviOlusturUseCase,
    YerlestirmeGoreviOverrideUseCase,
    YerlestirmeGoreviTamamlaUseCase,
    YerlestirmeGoreviYerlestirmeGoreviBekleyenOzetUseCase,
    YerlestirmeOnaylaUseCase,
    ZamanAsimiBirakUseCase,
)
from app.core.entities.mal_kabul_irsaliye import MalKabulDurum, MalKabulIrsaliye, MalKabulKalemi
from app.core.entities.yerlestirme_gorevi import GorevDurum, GorevTipi, YerlestirmeGorevi
from app.core.entities.zon import ZonTipi
from app.core.exceptions import (
    GecersizDurumGecisiError,
    GecersizIslemError,
    KayitBulunamadiError,
)

pytestmark = pytest.mark.unit


# ────────── yardımcılar ──────────

def _gorev(
    *,
    id: int = 1,
    durum: str = GorevDurum.BEKLIYOR,
    palet_id: int = 100,
    onerilen_raf_id: int = 10,
    atanan_kullanici_id: int | None = None,
    tip: str = GorevTipi.YERLESTIRME,
    mal_kabul_irsaliye_id: int | None = None,
    depo_id: int | None = 7,
    kaynak_raf_id: int | None = None,
) -> YerlestirmeGorevi:
    return YerlestirmeGorevi(
        id=id,
        palet_id=palet_id,
        mal_kabul_irsaliye_id=mal_kabul_irsaliye_id,
        depo_id=depo_id,
        tip=tip,
        kaynak_raf_id=kaynak_raf_id,
        onerilen_raf_id=onerilen_raf_id,
        durum=durum,
        oncelik=3,
        atanan_kullanici_id=atanan_kullanici_id,
        olusturma_tarihi=datetime(2026, 4, 1, 9, 0, 0),
    )


def _raf(id: int = 10, kod: str = "A-01-01", depo_id: int = 7, zon_id: int | None = 55, kapasite: int = 10):
    return SimpleNamespace(id=id, kod=kod, depo_id=depo_id, zon_id=zon_id, kapasite=kapasite)


def _palet(id: int = 100, palet_no: str = "P-001", aktif: bool = True, raf_id: int = 10, lot_id: int = 5, palet_kg: float = 120.0):
    return SimpleNamespace(
        id=id,
        palet_no=palet_no,
        aktif=aktif,
        raf_id=raf_id,
        lot_id=lot_id,
        palet_kg=palet_kg,
        raf_ata=lambda r: setattr(_palet, "_", r),  # yerine stub; gerçek raf_ata kullanmaya gerek yok
    )


class FakePalet:
    """Gerçek raf_ata davranışını modelleyen basit stub."""

    def __init__(self, id=100, palet_no="P-001", aktif=True, raf_id=10, lot_id=5, palet_kg=120.0):
        self.id = id
        self.palet_no = palet_no
        self.aktif = aktif
        self.raf_id = raf_id
        self.lot_id = lot_id
        self.palet_kg = palet_kg

    def raf_ata(self, raf_id: int) -> None:
        self.raf_id = raf_id


# ─────────────────────────────────────────────────────────────────
# LİSTELE / GETİR
# ─────────────────────────────────────────────────────────────────

class TestListeleGetir:
    def test_listele_repo_sonuclarini_dto_olarak_doner(self):
        repo = MagicMock()
        repo.getir_hepsi.return_value = [_gorev(id=1), _gorev(id=2, palet_id=101)]
        uc = YerlestirmeGoreviListeleUseCase(repo)

        sonuc = uc.execute(skip=0, limit=50, durum="Bekliyor", depo_id=7)

        assert len(sonuc) == 2
        assert sonuc[0].id == 1 and sonuc[1].id == 2
        repo.getir_hepsi.assert_called_once_with(
            skip=0, limit=50, durum="Bekliyor",
            atanan_kullanici_id=None, palet_id=None, depo_id=7,
        )

    def test_getir_bulunamazsa_kayit_bulunamadi(self):
        repo = MagicMock()
        repo.getir_id_ile.return_value = None
        uc = YerlestirmeGoreviGetirUseCase(repo)

        with pytest.raises(KayitBulunamadiError):
            uc.execute(gorev_id=42)

    def test_getir_bulursa_dto_doner(self):
        repo = MagicMock()
        repo.getir_id_ile.return_value = _gorev(id=9)
        uc = YerlestirmeGoreviGetirUseCase(repo)

        sonuc = uc.execute(gorev_id=9)
        assert sonuc.id == 9


# ─────────────────────────────────────────────────────────────────
# OLUŞTUR
# ─────────────────────────────────────────────────────────────────

class TestYerlestirmeGoreviOlustur:
    def _mocks(self):
        return {
            "repo": MagicMock(),
            "palet_repo": MagicMock(),
            "raf_repo": MagicMock(),
            "log_repo": MagicMock(),
        }

    def test_palet_yoksa_hata(self):
        m = self._mocks()
        m["palet_repo"].getir_id_ile.return_value = None
        uc = YerlestirmeGoreviOlusturUseCase(**m)

        dto = YerlestirmeGoreviOlusturRequestDTO(palet_id=1, onerilen_raf_id=10)
        with pytest.raises(KayitBulunamadiError):
            uc.execute(dto, kullanici_id=1)

        m["repo"].olustur.assert_not_called()

    def test_raf_yoksa_hata(self):
        m = self._mocks()
        m["palet_repo"].getir_id_ile.return_value = FakePalet()
        m["raf_repo"].getir_id_ile.return_value = None
        uc = YerlestirmeGoreviOlusturUseCase(**m)

        dto = YerlestirmeGoreviOlusturRequestDTO(palet_id=100, onerilen_raf_id=10)
        with pytest.raises(KayitBulunamadiError):
            uc.execute(dto, kullanici_id=1)

    def test_transfer_gorevi_kaynak_raf_zorunlu(self):
        m = self._mocks()
        m["palet_repo"].getir_id_ile.return_value = FakePalet()
        m["raf_repo"].getir_id_ile.return_value = _raf()
        uc = YerlestirmeGoreviOlusturUseCase(**m)

        dto = YerlestirmeGoreviOlusturRequestDTO(
            palet_id=100, onerilen_raf_id=10, tip=GorevTipi.TRANSFER,
        )
        with pytest.raises(GecersizIslemError, match="kaynak_raf_id"):
            uc.execute(dto, kullanici_id=1)

    def test_happy_path_gorev_olusturur_ve_log_atar(self):
        m = self._mocks()
        m["palet_repo"].getir_id_ile.return_value = FakePalet()
        m["raf_repo"].getir_id_ile.return_value = _raf(id=10, depo_id=7)
        m["repo"].olustur.side_effect = lambda g: (setattr(g, "id", 77) or g)
        uc = YerlestirmeGoreviOlusturUseCase(**m)

        dto = YerlestirmeGoreviOlusturRequestDTO(palet_id=100, onerilen_raf_id=10)
        sonuc = uc.execute(dto, kullanici_id=5)

        assert sonuc.id == 77
        assert sonuc.depo_id == 7
        m["repo"].olustur.assert_called_once()
        m["log_repo"].olustur.assert_called_once()


# ─────────────────────────────────────────────────────────────────
# SONRAKI / ZAMAN AŞIMI / BAŞLAT / BIRAK
# ─────────────────────────────────────────────────────────────────

class TestSonrakiVeTimeout:
    def test_sonraki_gorev_yoksa_none(self):
        repo = MagicMock()
        repo.sonraki_gorevi_kilitle.return_value = None
        uc = SonrakiGorevisiniAlUseCase(repo)
        assert uc.execute(kullanici_id=5) is None

    def test_sonraki_gorev_varsa_dto(self):
        repo = MagicMock()
        repo.sonraki_gorevi_kilitle.return_value = _gorev(id=11, durum=GorevDurum.ATANDI)
        uc = SonrakiGorevisiniAlUseCase(repo)

        sonuc = uc.execute(kullanici_id=5, depo_id=7)
        assert sonuc.id == 11
        repo.sonraki_gorevi_kilitle.assert_called_once_with(5, depo_id=7)

    def test_zaman_asimi_birak_serbest_sayisini_doner(self):
        repo = MagicMock()
        g1 = _gorev(id=1, durum=GorevDurum.ATANDI, atanan_kullanici_id=7)
        g1.atanma_tarihi = datetime.utcnow() - timedelta(minutes=120)
        g2 = _gorev(id=2, durum=GorevDurum.ATANDI, atanan_kullanici_id=8)
        g2.atanma_tarihi = datetime.utcnow() - timedelta(minutes=90)
        repo.getir_zaman_asimi_gecmis.return_value = [g1, g2]
        uc = ZamanAsimiBirakUseCase(repo, timeout_dk=60)

        sonuc = uc.execute()
        assert sonuc == {"serbest_birakildi": 2, "timeout_dk": 60}
        assert g1.durum == GorevDurum.BEKLIYOR
        assert g1.atanan_kullanici_id is None
        assert repo.guncelle.call_count == 2


class TestBaslatBirak:
    def test_baslat_bulunamayan_gorev(self):
        repo = MagicMock()
        repo.getir_id_ile.return_value = None
        uc = YerlestirmeGoreviBaslatUseCase(repo)
        with pytest.raises(KayitBulunamadiError):
            uc.execute(1, kullanici_id=5)

    def test_baslat_farkli_kullanici_reddedilir(self):
        repo = MagicMock()
        repo.getir_id_ile.return_value = _gorev(durum=GorevDurum.ATANDI, atanan_kullanici_id=10)
        uc = YerlestirmeGoreviBaslatUseCase(repo)
        with pytest.raises(GecersizIslemError, match="atanma"):
            uc.execute(1, kullanici_id=99)
        repo.guncelle.assert_not_called()

    def test_baslat_happy_path(self):
        repo = MagicMock()
        gorev = _gorev(durum=GorevDurum.ATANDI, atanan_kullanici_id=10)
        repo.getir_id_ile.return_value = gorev
        repo.guncelle.return_value = gorev
        uc = YerlestirmeGoreviBaslatUseCase(repo)

        sonuc = uc.execute(1, kullanici_id=10)
        assert sonuc.durum == GorevDurum.DEVAM_EDIYOR
        repo.guncelle.assert_called_once_with(gorev)

    def test_birak_atanan_olmayan_kullanici_reddedilir(self):
        repo = MagicMock()
        repo.getir_id_ile.return_value = _gorev(durum=GorevDurum.ATANDI, atanan_kullanici_id=10)
        uc = YerlestirmeGoreviBirakUseCase(repo)
        with pytest.raises(GecersizIslemError):
            uc.execute(1, kullanici_id=11)

    def test_birak_happy_path(self):
        repo = MagicMock()
        gorev = _gorev(durum=GorevDurum.ATANDI, atanan_kullanici_id=10)
        repo.getir_id_ile.return_value = gorev
        repo.guncelle.return_value = gorev
        uc = YerlestirmeGoreviBirakUseCase(repo)

        sonuc = uc.execute(1, kullanici_id=10)
        assert sonuc.durum == GorevDurum.BEKLIYOR


# ─────────────────────────────────────────────────────────────────
# TAMAMLA (+ irsaliye otomatik kapanış)
# ─────────────────────────────────────────────────────────────────

class TestTamamla:
    def _mocks(self):
        return {
            "repo": MagicMock(),
            "palet_repo": MagicMock(),
            "raf_repo": MagicMock(),
            "log_repo": MagicMock(),
            "mal_kabul_repo": MagicMock(),
        }

    def test_gorev_yoksa_hata(self):
        m = self._mocks()
        m["repo"].getir_id_ile.return_value = None
        uc = YerlestirmeGoreviTamamlaUseCase(**m)

        dto = YerlestirmeGoreviTamamlaRequestDTO(gerceklesen_raf_id=10)
        with pytest.raises(KayitBulunamadiError):
            uc.execute(1, dto, kullanici_id=5)

    def test_atanmamis_kullanici_reddedilir(self):
        m = self._mocks()
        m["repo"].getir_id_ile.return_value = _gorev(
            durum=GorevDurum.DEVAM_EDIYOR, atanan_kullanici_id=10,
        )
        uc = YerlestirmeGoreviTamamlaUseCase(**m)
        dto = YerlestirmeGoreviTamamlaRequestDTO(gerceklesen_raf_id=10)
        with pytest.raises(GecersizIslemError):
            uc.execute(1, dto, kullanici_id=99)

    def test_raf_yoksa_hata(self):
        m = self._mocks()
        m["repo"].getir_id_ile.return_value = _gorev(
            durum=GorevDurum.DEVAM_EDIYOR, atanan_kullanici_id=5,
        )
        m["raf_repo"].getir_id_ile.return_value = None
        uc = YerlestirmeGoreviTamamlaUseCase(**m)
        dto = YerlestirmeGoreviTamamlaRequestDTO(gerceklesen_raf_id=10)
        with pytest.raises(KayitBulunamadiError):
            uc.execute(1, dto, kullanici_id=5)

    def test_palet_yoksa_hata(self):
        m = self._mocks()
        m["repo"].getir_id_ile.return_value = _gorev(
            durum=GorevDurum.DEVAM_EDIYOR, atanan_kullanici_id=5,
        )
        m["raf_repo"].getir_id_ile.return_value = _raf()
        m["palet_repo"].getir_id_ile.return_value = None
        uc = YerlestirmeGoreviTamamlaUseCase(**m)
        dto = YerlestirmeGoreviTamamlaRequestDTO(gerceklesen_raf_id=10)
        with pytest.raises(KayitBulunamadiError):
            uc.execute(1, dto, kullanici_id=5)

    def test_gecersiz_durum_tamamlanamaz(self):
        """BEKLIYOR → TAMAMLANDI geçişi entity düzeyinde reddedilmeli."""
        m = self._mocks()
        m["repo"].getir_id_ile.return_value = _gorev(
            durum=GorevDurum.BEKLIYOR, atanan_kullanici_id=5,
        )
        m["raf_repo"].getir_id_ile.return_value = _raf()
        m["palet_repo"].getir_id_ile.return_value = FakePalet()
        uc = YerlestirmeGoreviTamamlaUseCase(**m)
        dto = YerlestirmeGoreviTamamlaRequestDTO(gerceklesen_raf_id=10)
        with pytest.raises(GecersizDurumGecisiError):
            uc.execute(1, dto, kullanici_id=5)

    def test_happy_path_palet_ve_gorev_guncellenir(self):
        m = self._mocks()
        gorev = _gorev(durum=GorevDurum.DEVAM_EDIYOR, atanan_kullanici_id=5)
        palet = FakePalet(raf_id=0)
        m["repo"].getir_id_ile.return_value = gorev
        m["repo"].guncelle.return_value = gorev
        m["raf_repo"].getir_id_ile.return_value = _raf(id=10, kod="B-01")
        m["palet_repo"].getir_id_ile.return_value = palet
        # mal_kabul_irsaliye_id None olduğundan otomatik kapanış devreye girmemeli
        uc = YerlestirmeGoreviTamamlaUseCase(**m)

        dto = YerlestirmeGoreviTamamlaRequestDTO(gerceklesen_raf_id=10)
        sonuc = uc.execute(1, dto, kullanici_id=5)

        assert palet.raf_id == 10
        assert gorev.durum == GorevDurum.TAMAMLANDI
        assert gorev.gerceklesen_raf_id == 10
        assert sonuc.durum == GorevDurum.TAMAMLANDI
        m["palet_repo"].guncelle.assert_called_once_with(palet, auto_commit=False)
        m["log_repo"].olustur.assert_called_once()
        m["mal_kabul_repo"].guncelle.assert_not_called()

    def test_irsaliye_son_gorev_kapaninca_kapat(self):
        """Tüm görevler TAMAMLANDI/IPTAL olduğunda irsaliye otomatik kapanır."""
        m = self._mocks()
        gorev = _gorev(
            id=1, durum=GorevDurum.DEVAM_EDIYOR,
            atanan_kullanici_id=5, mal_kabul_irsaliye_id=900,
        )
        palet = FakePalet()
        m["repo"].getir_id_ile.return_value = gorev
        m["repo"].guncelle.return_value = gorev
        m["raf_repo"].getir_id_ile.return_value = _raf()
        m["palet_repo"].getir_id_ile.return_value = palet

        diger_bitmis = _gorev(id=2, durum=GorevDurum.TAMAMLANDI)
        diger_bitmis.baslama_tarihi = datetime(2026, 4, 1, 10, 0)
        diger_bitmis.tamamlanma_tarihi = datetime(2026, 4, 1, 10, 15)
        m["repo"].getir_irsaliye_id_ile.return_value = [gorev, diger_bitmis]

        irsaliye = MalKabulIrsaliye(
            id=900, irsaliye_no="IRS-1", durum=MalKabulDurum.ONAYLANDI,
            kalemler=[MalKabulKalemi(), MalKabulKalemi()],
        )
        m["mal_kabul_repo"].getir_id_ile.return_value = irsaliye

        uc = YerlestirmeGoreviTamamlaUseCase(**m)
        dto = YerlestirmeGoreviTamamlaRequestDTO(gerceklesen_raf_id=10)
        uc.execute(1, dto, kullanici_id=5)

        assert irsaliye.durum == MalKabulDurum.KAPANDI
        assert irsaliye.kapanma_ozeti is not None
        assert irsaliye.kapanma_ozeti["toplam_kalem"] == 2
        assert irsaliye.kapanma_ozeti["yerlestirilen"] == 2
        m["mal_kabul_repo"].guncelle.assert_called_once()

    def test_irsaliye_hala_bekleyen_varsa_kapatmaz(self):
        m = self._mocks()
        gorev = _gorev(
            id=1, durum=GorevDurum.DEVAM_EDIYOR,
            atanan_kullanici_id=5, mal_kabul_irsaliye_id=900,
        )
        m["repo"].getir_id_ile.return_value = gorev
        m["repo"].guncelle.return_value = gorev
        m["raf_repo"].getir_id_ile.return_value = _raf()
        m["palet_repo"].getir_id_ile.return_value = FakePalet()

        bekleyen = _gorev(id=2, durum=GorevDurum.BEKLIYOR)
        m["repo"].getir_irsaliye_id_ile.return_value = [gorev, bekleyen]

        uc = YerlestirmeGoreviTamamlaUseCase(**m)
        uc.execute(1, YerlestirmeGoreviTamamlaRequestDTO(gerceklesen_raf_id=10), kullanici_id=5)

        m["mal_kabul_repo"].getir_id_ile.assert_not_called()
        m["mal_kabul_repo"].guncelle.assert_not_called()


# ─────────────────────────────────────────────────────────────────
# OVERRIDE (süpervizör)
# ─────────────────────────────────────────────────────────────────

class TestOverride:
    def _mocks(self):
        return {
            "repo": MagicMock(),
            "palet_repo": MagicMock(),
            "raf_repo": MagicMock(),
            "log_repo": MagicMock(),
            "mal_kabul_repo": MagicMock(),
        }

    def test_gorev_yoksa_hata(self):
        m = self._mocks()
        m["repo"].getir_id_ile.return_value = None
        uc = YerlestirmeGoreviOverrideUseCase(**m)
        dto = YerlestirmeGoreviOverrideRequestDTO(gerceklesen_raf_id=10, neden="sebep sebep")
        with pytest.raises(KayitBulunamadiError):
            uc.execute(1, dto, supervisor_id=99)

    def test_override_devam_eden_gorevi_tamamlar_ve_override_alanlarini_kaydeder(self):
        m = self._mocks()
        gorev = _gorev(durum=GorevDurum.DEVAM_EDIYOR, atanan_kullanici_id=5)
        palet = FakePalet(raf_id=0)
        m["repo"].getir_id_ile.return_value = gorev
        m["repo"].guncelle.return_value = gorev
        m["raf_repo"].getir_id_ile.return_value = _raf(id=20, kod="C-02")
        m["palet_repo"].getir_id_ile.return_value = palet

        uc = YerlestirmeGoreviOverrideUseCase(**m)
        dto = YerlestirmeGoreviOverrideRequestDTO(gerceklesen_raf_id=20, neden="Kapasite istisnasi")
        sonuc = uc.execute(1, dto, supervisor_id=99)

        assert gorev.durum == GorevDurum.TAMAMLANDI
        assert gorev.override_kullanici_id == 99
        assert gorev.override_neden == "Kapasite istisnasi"
        assert palet.raf_id == 20
        assert sonuc.override_kullanici_id == 99


# ─────────────────────────────────────────────────────────────────
# BEKLEYEN ÖZET
# ─────────────────────────────────────────────────────────────────

class TestBekleyenOzet:
    def test_onceliklere_gore_gruplar(self):
        repo = MagicMock()
        g1 = _gorev(id=1); g1.oncelik = 1
        g2 = _gorev(id=2); g2.oncelik = 2
        g3 = _gorev(id=3); g3.oncelik = 3
        g4 = _gorev(id=4); g4.oncelik = 5
        repo.getir_hepsi.return_value = [g1, g2, g3, g4]
        uc = YerlestirmeGoreviYerlestirmeGoreviBekleyenOzetUseCase(repo)

        ozet = uc.execute(depo_id=7)
        assert ozet == {
            "toplam_bekleyen": 4,
            "acil": 1,
            "yuksek_oncelikli": 1,
            "normal": 2,
        }
        repo.getir_hepsi.assert_called_once_with(durum="Bekliyor", limit=10000, depo_id=7)


# ─────────────────────────────────────────────────────────────────
# İPTAL
# ─────────────────────────────────────────────────────────────────

class TestIptal:
    def test_gorev_yoksa_hata(self):
        repo = MagicMock(); log = MagicMock()
        repo.getir_id_ile.return_value = None
        uc = YerlestirmeGoreviIptalUseCase(repo, log)
        with pytest.raises(KayitBulunamadiError):
            uc.execute(1, YerlestirmeGoreviIptalRequestDTO(neden="n"), kullanici_id=1)

    def test_tamamlanmis_gorev_iptal_edilemez(self):
        repo = MagicMock(); log = MagicMock()
        repo.getir_id_ile.return_value = _gorev(durum=GorevDurum.TAMAMLANDI)
        uc = YerlestirmeGoreviIptalUseCase(repo, log)
        with pytest.raises(GecersizDurumGecisiError):
            uc.execute(1, YerlestirmeGoreviIptalRequestDTO(neden="n"), kullanici_id=1)

    def test_happy_path_iptal(self):
        repo = MagicMock(); log = MagicMock()
        gorev = _gorev(durum=GorevDurum.BEKLIYOR)
        repo.getir_id_ile.return_value = gorev
        repo.guncelle.return_value = gorev
        uc = YerlestirmeGoreviIptalUseCase(repo, log)

        sonuc = uc.execute(1, YerlestirmeGoreviIptalRequestDTO(neden="operasyonel"), kullanici_id=5)
        assert sonuc.durum == GorevDurum.IPTAL_EDILDI
        assert gorev.iptal_nedeni == "operasyonel"
        log.olustur.assert_called_once()


# ─────────────────────────────────────────────────────────────────
# SCAN-TO-VERIFY (YerlestirmeOnayla)
# ─────────────────────────────────────────────────────────────────

class TestYerlestirmeOnayla:
    def _mocks(self):
        return {
            "repo": MagicMock(),
            "palet_repo": MagicMock(),
            "raf_repo": MagicMock(),
            "lot_repo": MagicMock(),
            "urun_repo": MagicMock(),
            "zon_repo": MagicMock(),
            "zon_uyumluluk": MagicMock(),
            "kapasite": MagicMock(),
            "log_repo": MagicMock(),
            "mal_kabul_repo": MagicMock(),
        }

    def _dto(self):
        return YerlestirmeOnaylaRequestDTO(okutulan_raf_kodu="A-01")

    def test_gorev_yoksa_hata(self):
        m = self._mocks()
        m["repo"].getir_id_ile.return_value = None
        uc = YerlestirmeOnaylaUseCase(**m)
        with pytest.raises(KayitBulunamadiError):
            uc.execute(1, self._dto(), kullanici_id=5)

    def test_farkli_operator_reddedilir(self):
        m = self._mocks()
        m["repo"].getir_id_ile.return_value = _gorev(
            durum=GorevDurum.DEVAM_EDIYOR, atanan_kullanici_id=5,
        )
        uc = YerlestirmeOnaylaUseCase(**m)
        with pytest.raises(GecersizIslemError, match="atan"):
            uc.execute(1, self._dto(), kullanici_id=99)

    def test_depo_id_cozumlenemiyorsa_hata(self):
        m = self._mocks()
        gorev = _gorev(atanan_kullanici_id=5, depo_id=None, onerilen_raf_id=0, kaynak_raf_id=None)
        gorev.durum = GorevDurum.DEVAM_EDIYOR
        m["repo"].getir_id_ile.return_value = gorev
        m["raf_repo"].getir_id_ile.return_value = None  # öneri/kaynak rafları da bulunamaz
        uc = YerlestirmeOnaylaUseCase(**m)
        with pytest.raises(GecersizIslemError, match="depo"):
            uc.execute(1, self._dto(), kullanici_id=5)

    def test_raf_kod_bulunamazsa_hata(self):
        m = self._mocks()
        m["repo"].getir_id_ile.return_value = _gorev(
            durum=GorevDurum.DEVAM_EDIYOR, atanan_kullanici_id=5,
        )
        m["raf_repo"].getir_kod_ile.return_value = None
        uc = YerlestirmeOnaylaUseCase(**m)
        with pytest.raises(KayitBulunamadiError):
            uc.execute(1, self._dto(), kullanici_id=5)

    def test_zon_uyumsuz_override_gerekli_doner(self):
        m = self._mocks()
        gorev = _gorev(durum=GorevDurum.DEVAM_EDIYOR, atanan_kullanici_id=5)
        palet = FakePalet()
        m["repo"].getir_id_ile.return_value = gorev
        m["raf_repo"].getir_kod_ile.return_value = _raf(id=20, zon_id=55)
        m["raf_repo"].getir_id_ile.return_value = _raf(id=10)
        m["palet_repo"].getir_id_ile.return_value = palet
        m["lot_repo"].getir_id_ile.return_value = SimpleNamespace(urun_id=501)
        m["urun_repo"].getir_id_ile.return_value = SimpleNamespace(
            id=501, depolama_tipi="Soguk"
        )
        m["zon_repo"].getir_id_ile.return_value = SimpleNamespace(tip=ZonTipi.TEHLIKELI)
        m["zon_uyumluluk"].uyumlu_mu.return_value = False
        m["zon_uyumluluk"].uyumsuzluk_mesaji.return_value = "Uyumsuz"
        m["kapasite"].alternatif_raflar_getir.return_value = []
        uc = YerlestirmeOnaylaUseCase(**m)

        sonuc = uc.execute(1, self._dto(), kullanici_id=5)

        assert sonuc.basarili is False
        assert sonuc.hata_tipi == "ZON_UYUMSUZ"
        assert sonuc.override_gerekli is True
        # Görev ve palet güncellenmemeli
        m["palet_repo"].guncelle.assert_not_called()
        assert gorev.durum == GorevDurum.DEVAM_EDIYOR

    def test_kapasite_yetersiz_alternatifler_doner(self):
        m = self._mocks()
        gorev = _gorev(durum=GorevDurum.DEVAM_EDIYOR, atanan_kullanici_id=5)
        palet = FakePalet(palet_kg=200.0)
        alt_raf = _raf(id=30, kod="D-01", kapasite=5)
        m["repo"].getir_id_ile.return_value = gorev
        m["raf_repo"].getir_kod_ile.return_value = _raf(id=20, zon_id=55)
        m["raf_repo"].getir_id_ile.return_value = _raf(id=10)
        m["palet_repo"].getir_id_ile.return_value = palet
        m["lot_repo"].getir_id_ile.return_value = SimpleNamespace(urun_id=501)
        m["urun_repo"].getir_id_ile.return_value = SimpleNamespace(
            id=501, depolama_tipi="Kuru"
        )
        m["zon_repo"].getir_id_ile.return_value = SimpleNamespace(tip=ZonTipi.GENEL)
        m["zon_uyumluluk"].uyumlu_mu.return_value = True
        m["kapasite"].dogrula.return_value = SimpleNamespace(yeterli=False, neden="Ağırlık aşıldı")
        m["kapasite"].alternatif_raflar_getir.return_value = [alt_raf]
        m["kapasite"].doluluk_orani.return_value = 0.7
        m["palet_repo"].getir_hepsi.return_value = [FakePalet(id=i) for i in range(3)]
        uc = YerlestirmeOnaylaUseCase(**m)

        sonuc = uc.execute(1, self._dto(), kullanici_id=5)

        assert sonuc.basarili is False
        assert sonuc.hata_tipi == "KAPASITE_YETERSIZ"
        assert len(sonuc.alternatifler) == 1
        assert sonuc.alternatifler[0].raf_id == 30
        assert sonuc.alternatifler[0].bos_slot == 2  # kapasite 5 - 3 palet

    def test_happy_path_tamamlar_ve_palet_rafa_atanir(self):
        m = self._mocks()
        gorev = _gorev(durum=GorevDurum.DEVAM_EDIYOR, atanan_kullanici_id=5)
        palet = FakePalet(raf_id=0)
        m["repo"].getir_id_ile.return_value = gorev
        m["raf_repo"].getir_kod_ile.return_value = _raf(id=20, kod="A-01", zon_id=55)
        m["raf_repo"].getir_id_ile.return_value = _raf(id=10)
        m["palet_repo"].getir_id_ile.return_value = palet
        m["lot_repo"].getir_id_ile.return_value = SimpleNamespace(urun_id=501)
        m["urun_repo"].getir_id_ile.return_value = SimpleNamespace(
            id=501, depolama_tipi="Kuru"
        )
        m["zon_repo"].getir_id_ile.return_value = SimpleNamespace(tip=ZonTipi.GENEL)
        m["zon_uyumluluk"].uyumlu_mu.return_value = True
        m["kapasite"].dogrula.return_value = SimpleNamespace(yeterli=True, neden=None)
        uc = YerlestirmeOnaylaUseCase(**m)

        sonuc = uc.execute(1, self._dto(), kullanici_id=5)

        assert sonuc.basarili is True
        assert sonuc.durum == "TAMAMLANDI"
        assert gorev.durum == GorevDurum.TAMAMLANDI
        assert gorev.gerceklesen_raf_id == 20
        assert palet.raf_id == 20


# ─────────────────────────────────────────────────────────────────
# BİLİNMEYEN KONUM GÖREVLERİ (STAGING)
# ─────────────────────────────────────────────────────────────────

class TestBilinmeyenKonum:
    def _mocks(self):
        return {
            "repo": MagicMock(),
            "palet_repo": MagicMock(),
            "raf_repo": MagicMock(),
            "lot_repo": MagicMock(),
            "urun_repo": MagicMock(),
            "algoritma": MagicMock(),
            "log_repo": MagicMock(),
        }

    def test_staging_raf_yoksa_hata(self):
        m = self._mocks()
        m["raf_repo"].getir_staging_raf.return_value = None
        uc = BilinmeyenKonumGorevleriOlusturUseCase(**m)
        with pytest.raises(GecersizIslemError, match="MIGRATION_STAGING"):
            uc.execute(depo_id=7, kullanici_id=1)

    def test_urunu_bulunamayan_palet_atlanir_ve_uyari_eklenir(self):
        m = self._mocks()
        m["raf_repo"].getir_staging_raf.return_value = _raf(id=99, kod="STAGING")
        m["palet_repo"].getir_hepsi.return_value = [FakePalet(id=1, palet_no="P-1", lot_id=None)]
        m["lot_repo"].getir_id_ile.return_value = None
        m["urun_repo"].getir_id_ile.return_value = None
        uc = BilinmeyenKonumGorevleriOlusturUseCase(**m)

        sonuc = uc.execute(depo_id=7, kullanici_id=1)
        assert sonuc.olusturulan_gorev_sayisi == 0
        assert sonuc.palet_sayisi == 1
        assert any("ürün bilgisi" in u for u in sonuc.uyari_mesajlari)

    def test_algoritma_oneri_yoksa_atlanir(self):
        m = self._mocks()
        m["raf_repo"].getir_staging_raf.return_value = _raf(id=99)
        m["palet_repo"].getir_hepsi.return_value = [FakePalet(id=1, palet_no="P-1", lot_id=5)]
        m["lot_repo"].getir_id_ile.return_value = SimpleNamespace(urun_id=501)
        m["urun_repo"].getir_id_ile.return_value = SimpleNamespace(id=501, depolama_tipi="Kuru")
        m["algoritma"].raf_oner.return_value = None
        uc = BilinmeyenKonumGorevleriOlusturUseCase(**m)

        sonuc = uc.execute(depo_id=7, kullanici_id=1)
        assert sonuc.olusturulan_gorev_sayisi == 0
        assert any("uygun raf" in u for u in sonuc.uyari_mesajlari)
        m["repo"].olustur.assert_not_called()

    def test_happy_path_gorev_olusturur(self):
        m = self._mocks()
        m["raf_repo"].getir_staging_raf.return_value = _raf(id=99)
        m["palet_repo"].getir_hepsi.return_value = [
            FakePalet(id=1, palet_no="P-1", lot_id=5),
            FakePalet(id=2, palet_no="P-2", lot_id=5),
        ]
        m["lot_repo"].getir_id_ile.return_value = SimpleNamespace(urun_id=501)
        m["urun_repo"].getir_id_ile.return_value = SimpleNamespace(id=501, depolama_tipi="Kuru")
        m["algoritma"].raf_oner.return_value = SimpleNamespace(
            onerilen_raf=SimpleNamespace(id=77)
        )
        uc = BilinmeyenKonumGorevleriOlusturUseCase(**m)

        sonuc = uc.execute(depo_id=7, kullanici_id=1)
        assert sonuc.olusturulan_gorev_sayisi == 2
        assert m["repo"].olustur.call_count == 2


# ─────────────────────────────────────────────────────────────────
# KARANTİNA
# ─────────────────────────────────────────────────────────────────

class TestKarantinadanCikar:
    def _mocks(self):
        return {
            "repo": MagicMock(),
            "palet_repo": MagicMock(),
            "raf_repo": MagicMock(),
            "lot_repo": MagicMock(),
            "urun_repo": MagicMock(),
            "zon_repo": MagicMock(),
            "algoritma": MagicMock(),
            "log_repo": MagicMock(),
        }

    def test_palet_yoksa_hata(self):
        m = self._mocks()
        m["palet_repo"].getir_id_ile.return_value = None
        uc = KarantinadanCikarUseCase(**m)
        with pytest.raises(KayitBulunamadiError):
            uc.execute(KarantinadanCikarRequestDTO(palet_id=1), kullanici_id=1)

    def test_pasif_palet_reddedilir(self):
        m = self._mocks()
        m["palet_repo"].getir_id_ile.return_value = FakePalet(aktif=False)
        uc = KarantinadanCikarUseCase(**m)
        with pytest.raises(GecersizIslemError, match="Pasif"):
            uc.execute(KarantinadanCikarRequestDTO(palet_id=1), kullanici_id=1)

    def test_karantinada_olmayan_palet_reddedilir(self):
        m = self._mocks()
        m["palet_repo"].getir_id_ile.return_value = FakePalet()
        m["raf_repo"].getir_id_ile.return_value = _raf(zon_id=55)
        m["zon_repo"].getir_id_ile.return_value = SimpleNamespace(
            tip=ZonTipi.GENEL, depo_id=7,
        )
        uc = KarantinadanCikarUseCase(**m)
        with pytest.raises(GecersizIslemError, match="karantina"):
            uc.execute(KarantinadanCikarRequestDTO(palet_id=1), kullanici_id=1)

    def test_uygun_hedef_raf_yoksa_hata(self):
        m = self._mocks()
        m["palet_repo"].getir_id_ile.return_value = FakePalet()
        m["raf_repo"].getir_id_ile.return_value = _raf(zon_id=55)
        m["zon_repo"].getir_id_ile.return_value = SimpleNamespace(
            tip=ZonTipi.KARANTINA, depo_id=7,
        )
        m["lot_repo"].getir_id_ile.return_value = SimpleNamespace(urun_id=501)
        m["urun_repo"].getir_id_ile.return_value = SimpleNamespace(id=501, depolama_tipi="Kuru")
        m["algoritma"].raf_oner.return_value = None
        uc = KarantinadanCikarUseCase(**m)
        with pytest.raises(GecersizIslemError, match="uygun hedef"):
            uc.execute(KarantinadanCikarRequestDTO(palet_id=1), kullanici_id=1)

    def test_happy_path_transfer_gorevi_olusturur(self):
        m = self._mocks()
        m["palet_repo"].getir_id_ile.return_value = FakePalet()
        m["raf_repo"].getir_id_ile.return_value = _raf(id=10, zon_id=55, depo_id=7)
        m["zon_repo"].getir_id_ile.return_value = SimpleNamespace(
            tip=ZonTipi.KARANTINA, depo_id=7,
        )
        m["lot_repo"].getir_id_ile.return_value = SimpleNamespace(urun_id=501)
        m["urun_repo"].getir_id_ile.return_value = SimpleNamespace(id=501, depolama_tipi="Kuru")
        m["algoritma"].raf_oner.return_value = SimpleNamespace(
            onerilen_raf=SimpleNamespace(id=200)
        )
        m["repo"].olustur.side_effect = lambda g: (setattr(g, "id", 55) or g)
        uc = KarantinadanCikarUseCase(**m)

        sonuc = uc.execute(KarantinadanCikarRequestDTO(palet_id=1), kullanici_id=1)
        assert sonuc.id == 55
        assert sonuc.tip == GorevTipi.TRANSFER
        assert sonuc.onerilen_raf_id == 200


class TestKarantinayaAl:
    def _mocks(self):
        return {
            "repo": MagicMock(),
            "palet_repo": MagicMock(),
            "raf_repo": MagicMock(),
            "zon_repo": MagicMock(),
            "kapasite": MagicMock(),
            "log_repo": MagicMock(),
        }

    def test_pasif_palet_reddedilir(self):
        m = self._mocks()
        m["palet_repo"].getir_id_ile.return_value = FakePalet(aktif=False)
        uc = KarantinayaAlUseCase(**m)
        with pytest.raises(GecersizIslemError, match="Pasif"):
            uc.execute(KarantinayaAlRequestDTO(palet_id=1, neden="hasar"), kullanici_id=1)

    def test_zaten_karantina_zonundaysa_reddedilir(self):
        m = self._mocks()
        m["palet_repo"].getir_id_ile.return_value = FakePalet()
        m["raf_repo"].getir_id_ile.return_value = _raf(zon_id=55, depo_id=7)
        m["zon_repo"].getir_id_ile.return_value = SimpleNamespace(
            tip=ZonTipi.KARANTINA, depo_id=7,
        )
        uc = KarantinayaAlUseCase(**m)
        with pytest.raises(GecersizIslemError, match="zaten"):
            uc.execute(KarantinayaAlRequestDTO(palet_id=1, neden="hasar"), kullanici_id=1)

    def test_uygun_karantina_raf_yoksa_hata(self):
        m = self._mocks()
        m["palet_repo"].getir_id_ile.return_value = FakePalet()
        m["raf_repo"].getir_id_ile.return_value = _raf(zon_id=55, depo_id=7)
        m["zon_repo"].getir_id_ile.return_value = SimpleNamespace(
            tip=ZonTipi.GENEL, depo_id=7,
        )
        # Karantina zonu arar ama bulamaz
        m["zon_repo"].getir_hepsi.return_value = []
        uc = KarantinayaAlUseCase(**m)
        with pytest.raises(GecersizIslemError, match="Karantina"):
            uc.execute(KarantinayaAlRequestDTO(palet_id=1, neden="hasar"), kullanici_id=1)

    def test_happy_path_transfer_gorevi_olusturur(self):
        m = self._mocks()
        m["palet_repo"].getir_id_ile.return_value = FakePalet()
        m["raf_repo"].getir_id_ile.return_value = _raf(id=10, zon_id=55, depo_id=7)
        # Mevcut zon KARANTINA değil → geçebilir
        m["zon_repo"].getir_id_ile.return_value = SimpleNamespace(
            tip=ZonTipi.GENEL, depo_id=7,
        )
        # Depodaki zon listesi: bir karantina zonu
        kar_zon = SimpleNamespace(id=555, tip=ZonTipi.KARANTINA, depo_id=7)
        m["zon_repo"].getir_hepsi.return_value = [kar_zon]
        kar_raf = _raf(id=999, zon_id=555, depo_id=7)
        m["raf_repo"].getir_hepsi.return_value = [kar_raf]
        m["kapasite"].dogrula.return_value = SimpleNamespace(yeterli=True, neden=None)
        m["repo"].olustur.side_effect = lambda g: (setattr(g, "id", 11) or g)
        uc = KarantinayaAlUseCase(**m)

        sonuc = uc.execute(KarantinayaAlRequestDTO(palet_id=1, neden="hasarli"), kullanici_id=1)
        assert sonuc.id == 11
        assert sonuc.tip == GorevTipi.TRANSFER
        assert sonuc.onerilen_raf_id == 999
        assert sonuc.oncelik == 1
