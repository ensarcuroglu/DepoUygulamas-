"""
Unit testler: YerlestirmeGorevi domain entity — durum geçiş state machine.

Kapsam:
- Geçerli tüm durum geçişleri
- Geçersiz geçişler GecersizDurumGecisiError fırlatmalı
- İş metodları (ata, baslat, bırak, tamamla, override_ile_tamamla, iptal_et)
- onerilen_raf_farkli_mi yardımcı metodu
"""

import pytest
from datetime import datetime

from app.core.entities.yerlestirme_gorevi import GorevDurum, YerlestirmeGorevi
from app.core.exceptions import GecersizDurumGecisiError

pytestmark = pytest.mark.unit


def _gorev(**kwargs) -> YerlestirmeGorevi:
    defaults = dict(id=1, palet_id=10, onerilen_raf_id=5, oncelik=5)
    return YerlestirmeGorevi(**{**defaults, **kwargs})


# ─── Geçerli Geçişler ──────────────────────────────────────────────────────

class TestGecerliGecisler:
    def test_bekliyor_atandi(self):
        g = _gorev()
        g.ata(kullanici_id=42)
        assert g.durum == GorevDurum.ATANDI
        assert g.atanan_kullanici_id == 42
        assert g.atanma_tarihi is not None
        assert g.baslama_tarihi is None

    def test_atandi_devam_ediyor(self):
        g = _gorev(durum=GorevDurum.ATANDI, atanan_kullanici_id=1)
        g.baslat()
        assert g.durum == GorevDurum.DEVAM_EDIYOR
        assert g.baslama_tarihi is not None

    def test_atandi_bekliyor_birak(self):
        g = _gorev(durum=GorevDurum.ATANDI, atanan_kullanici_id=7)
        g.bırak()
        assert g.durum == GorevDurum.BEKLIYOR
        assert g.atanan_kullanici_id is None
        assert g.baslama_tarihi is None

    def test_devam_ediyor_tamamlandi(self):
        g = _gorev(durum=GorevDurum.DEVAM_EDIYOR, atanan_kullanici_id=1)
        g.tamamla(gerceklesen_raf_id=99)
        assert g.durum == GorevDurum.TAMAMLANDI
        assert g.gerceklesen_raf_id == 99
        assert g.tamamlanma_tarihi is not None

    def test_devam_ediyor_iptal(self):
        g = _gorev(durum=GorevDurum.DEVAM_EDIYOR, atanan_kullanici_id=1)
        g.iptal_et(neden="Palet hasar gördü")
        assert g.durum == GorevDurum.IPTAL_EDILDI
        assert g.iptal_nedeni == "Palet hasar gördü"

    def test_bekliyor_iptal(self):
        g = _gorev()
        g.iptal_et(neden="Test iptali")
        assert g.durum == GorevDurum.IPTAL_EDILDI

    def test_atandi_iptal(self):
        g = _gorev(durum=GorevDurum.ATANDI, atanan_kullanici_id=1)
        g.iptal_et(neden="Operatör müsait değil")
        assert g.durum == GorevDurum.IPTAL_EDILDI

    def test_override_ile_tamamla(self):
        g = _gorev(durum=GorevDurum.DEVAM_EDIYOR, atanan_kullanici_id=1)
        g.override_ile_tamamla(
            gerceklesen_raf_id=200,
            supervisor_id=99,
            neden="Kapasite istisnası — süpervizör onayladı",
        )
        assert g.durum == GorevDurum.TAMAMLANDI
        assert g.gerceklesen_raf_id == 200
        assert g.override_kullanici_id == 99
        assert g.override_neden == "Kapasite istisnası — süpervizör onayladı"


# ─── Geçersiz Geçişler ─────────────────────────────────────────────────────

class TestGecersizGecisler:
    @pytest.mark.parametrize("baslangic,metot,kwargs", [
        # Tamamlanan görev artık geçiş kabul etmez
        (GorevDurum.TAMAMLANDI, "iptal_et", {"neden": "x"}),
        # İptal edilen görev artık geçiş kabul etmez
        (GorevDurum.IPTAL_EDILDI, "iptal_et", {"neden": "x"}),
        # Bekliyor → baslat doğrudan geçersiz (ata → baslat sırası olmalı)
        (GorevDurum.BEKLIYOR, "baslat", {}),
        # Devam ediyor → ata geçersiz
        (GorevDurum.DEVAM_EDIYOR, "ata", {"kullanici_id": 1}),
        # Tamamlandi → tamamla geçersiz
        (GorevDurum.TAMAMLANDI, "tamamla", {"gerceklesen_raf_id": 1}),
    ])
    def test_gecersiz_gecis(self, baslangic, metot, kwargs):
        g = _gorev(durum=baslangic)
        with pytest.raises(GecersizDurumGecisiError):
            getattr(g, metot)(**kwargs)

    def test_tamamlandi_override_gecersiz(self):
        g = _gorev(durum=GorevDurum.TAMAMLANDI)
        with pytest.raises(GecersizDurumGecisiError):
            g.override_ile_tamamla(
                gerceklesen_raf_id=1, supervisor_id=1, neden="geç onay"
            )

    def test_bekliyor_birak_gecersiz(self):
        """Bekliyor durumundan bırak (ATANDI→BEKLIYOR) geçişi geçersiz."""
        g = _gorev(durum=GorevDurum.BEKLIYOR)
        with pytest.raises(GecersizDurumGecisiError):
            g.bırak()


# ─── gecis_gecerli_mi yardımcı metodu ─────────────────────────────────────

class TestGecisGecerliMi:
    @pytest.mark.parametrize("mevcut,hedef,beklenen", [
        (GorevDurum.BEKLIYOR, GorevDurum.ATANDI, True),
        (GorevDurum.BEKLIYOR, GorevDurum.IPTAL_EDILDI, True),
        (GorevDurum.BEKLIYOR, GorevDurum.DEVAM_EDIYOR, False),
        (GorevDurum.ATANDI, GorevDurum.DEVAM_EDIYOR, True),
        (GorevDurum.ATANDI, GorevDurum.BEKLIYOR, True),
        (GorevDurum.ATANDI, GorevDurum.IPTAL_EDILDI, True),
        (GorevDurum.DEVAM_EDIYOR, GorevDurum.TAMAMLANDI, True),
        (GorevDurum.DEVAM_EDIYOR, GorevDurum.IPTAL_EDILDI, True),
        (GorevDurum.DEVAM_EDIYOR, GorevDurum.BEKLIYOR, False),
        (GorevDurum.TAMAMLANDI, GorevDurum.IPTAL_EDILDI, False),
        (GorevDurum.IPTAL_EDILDI, GorevDurum.BEKLIYOR, False),
    ])
    def test_gecis_gecerli_mi(self, mevcut, hedef, beklenen):
        assert GorevDurum.gecis_gecerli_mi(mevcut, hedef) is beklenen

    def test_bilinmeyen_durum_gecersiz(self):
        assert GorevDurum.gecis_gecerli_mi("BilinmeyenDurum", GorevDurum.ATANDI) is False


# ─── onerilen_raf_farkli_mi ────────────────────────────────────────────────

class TestOnerildenFarkliMi:
    def test_gerceklesen_yok_false(self):
        g = _gorev(onerilen_raf_id=5, gerceklesen_raf_id=None)
        assert g.onerilen_raf_farkli_mi() is False

    def test_gerceklesen_ayni_false(self):
        g = _gorev(onerilen_raf_id=5, gerceklesen_raf_id=5)
        assert g.onerilen_raf_farkli_mi() is False

    def test_gerceklesen_farkli_true(self):
        g = _gorev(onerilen_raf_id=5, gerceklesen_raf_id=99)
        assert g.onerilen_raf_farkli_mi() is True
