"""Unit testler — OperatorPerformansSorguUseCase.

Mock repo ile saf use case davranışı: sıralama, /me bugün ayrımı, leaderboard
sıra/limit kuralları, tarih varsayılanı.
"""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest

from app.application.use_cases import OperatorPerformansSorguUseCase
from app.core.entities.operator_performans import OperatorVardiyaMetrikleri

pytestmark = pytest.mark.unit


def _metrik(
    kullanici_id: int,
    yerlestirme: int = 0,
    toplama: int = 0,
    aktif_sn: int = 0,
    iptal: int = 0,
    vardiya: date | None = None,
    operator_adi: str | None = None,
    depo_id: int | None = None,
) -> OperatorVardiyaMetrikleri:
    m = OperatorVardiyaMetrikleri(
        kullanici_id=kullanici_id,
        depo_id=depo_id,
        vardiya_tarihi=vardiya or date.today(),
        tamamlanan_yerlestirme=yerlestirme,
        tamamlanan_toplama=toplama,
        toplam_aktif_saniye=aktif_sn,
        iptal_sayisi=iptal,
    )
    m.operator_adi = operator_adi
    return m


class TestOzetGetir:
    def test_repo_cikartisi_dto_ya_donusur(self) -> None:
        repo = MagicMock()
        repo.getir_aralik.return_value = [
            _metrik(7, yerlestirme=10, aktif_sn=3600, operator_adi="A. B."),
            _metrik(8, toplama=5, aktif_sn=1800, operator_adi="C. D."),
        ]
        uc = OperatorPerformansSorguUseCase(repo)
        sonuc = uc.ozet_getir(limit=50)

        assert sonuc.toplam == 2
        assert sonuc.items[0].kullanici_id == 7
        assert sonuc.items[0].uph == 10.0
        assert sonuc.items[1].uph == 10.0  # 5 / 0.5h

    def test_filtre_repoya_aktariliyor(self) -> None:
        repo = MagicMock()
        repo.getir_aralik.return_value = []
        uc = OperatorPerformansSorguUseCase(repo)
        baslangic = date(2026, 5, 1)
        bitis = date(2026, 5, 7)

        uc.ozet_getir(
            baslangic=baslangic, bitis=bitis, depo_id=3, kullanici_id=7,
            skip=10, limit=25,
        )
        repo.getir_aralik.assert_called_once_with(
            kullanici_id=7,
            depo_id=3,
            baslangic=baslangic,
            bitis=bitis,
            skip=10,
            limit=25,
        )


class TestKullaniciDetay:
    def test_aralik_repoya_aktariliyor(self) -> None:
        repo = MagicMock()
        repo.getir_aralik.return_value = []
        uc = OperatorPerformansSorguUseCase(repo)

        uc.kullanici_detay_getir(
            kullanici_id=7, baslangic=date(2026, 5, 1), bitis=date(2026, 5, 7)
        )
        repo.getir_aralik.assert_called_once_with(
            kullanici_id=7,
            baslangic=date(2026, 5, 1),
            bitis=date(2026, 5, 7),
            skip=0,
            limit=90,
        )


class TestLeaderboard:
    def test_uph_azalan_siralanir_sira_atanir(self) -> None:
        repo = MagicMock()
        # Üç operatör — kasıtlı karışık sırada veriyoruz
        repo.leaderboard_getir.return_value = [
            _metrik(8, toplama=10, aktif_sn=3600),  # UPH=10
            _metrik(7, yerlestirme=20, aktif_sn=3600),  # UPH=20
            _metrik(9, yerlestirme=5, aktif_sn=3600),  # UPH=5
        ]
        uc = OperatorPerformansSorguUseCase(repo)
        gun = date(2026, 5, 6)

        sonuc = uc.leaderboard_getir(vardiya_tarihi=gun, limit=10)

        assert sonuc.vardiya_tarihi == gun
        assert [i.kullanici_id for i in sonuc.items] == [7, 8, 9]
        assert [i.sira for i in sonuc.items] == [1, 2, 3]
        assert sonuc.items[0].uph == 20.0

    def test_limit_uygulanir(self) -> None:
        repo = MagicMock()
        repo.leaderboard_getir.return_value = [
            _metrik(i, yerlestirme=i, aktif_sn=3600) for i in range(1, 11)
        ]
        uc = OperatorPerformansSorguUseCase(repo)
        sonuc = uc.leaderboard_getir(limit=3)
        assert len(sonuc.items) == 3
        # En yüksek UPH olanlar (10, 9, 8)
        assert [i.kullanici_id for i in sonuc.items] == [10, 9, 8]

    def test_vardiya_tarihi_yoksa_bugun_kullanilir(self) -> None:
        repo = MagicMock()
        repo.leaderboard_getir.return_value = []
        uc = OperatorPerformansSorguUseCase(repo)

        sonuc = uc.leaderboard_getir()
        assert sonuc.vardiya_tarihi == date.today()
        repo.leaderboard_getir.assert_called_once()
        assert repo.leaderboard_getir.call_args.kwargs["vardiya_tarihi"] == date.today()


class TestKendiMetriklerim:
    def test_bugun_ayrilarak_donulur(self) -> None:
        repo = MagicMock()
        bugun = date.today()
        dun = bugun - timedelta(days=1)
        repo.getir_aralik.return_value = [
            _metrik(7, yerlestirme=3, aktif_sn=600, vardiya=bugun),
            _metrik(7, yerlestirme=2, aktif_sn=400, vardiya=dun),
        ]
        uc = OperatorPerformansSorguUseCase(repo)

        sonuc = uc.kendi_metriklerim(kullanici_id=7, gun_sayisi=7)
        assert sonuc.bugun is not None
        assert sonuc.bugun.vardiya_tarihi == bugun
        assert len(sonuc.son_gunler) == 2

    def test_bugun_yoksa_none(self) -> None:
        repo = MagicMock()
        gecmis = date.today() - timedelta(days=2)
        repo.getir_aralik.return_value = [
            _metrik(7, yerlestirme=2, aktif_sn=400, vardiya=gecmis),
        ]
        uc = OperatorPerformansSorguUseCase(repo)

        sonuc = uc.kendi_metriklerim(kullanici_id=7, gun_sayisi=7)
        assert sonuc.bugun is None
        assert len(sonuc.son_gunler) == 1
