import pytest
from unittest.mock import MagicMock

# Proje yapına göre import yollarını kontrol et
from app.core.entities.mal_kabul_irsaliye import (
    MalKabulIrsaliye, MalKabulDurum, MalKabulKalemi, KalemDurum
)
from app.infrastructure.services.irsaliye_palet_veri_kaynagi_service import IrsaliyePaletVeriKaynagiService
from app.core.exceptions import GecersizIslemError

@pytest.fixture
def mock_repos():
    """Tüm repository'leri mock olarak hazırlayan fixture."""
    return {
        "mal_kabul": MagicMock(),
        "urun": MagicMock(),
        "depo": MagicMock(),
        "raf": MagicMock(),
        "lot": MagicMock()
    }

@pytest.fixture
def service(mock_repos):
    """Test edilecek servisi mock bağımlılıklarla başlatır."""
    return IrsaliyePaletVeriKaynagiService(
        mal_kabul_repo=mock_repos["mal_kabul"],
        urun_repo=mock_repos["urun"],
        depo_repo=mock_repos["depo"],
        raf_repo=mock_repos["raf"],
        lot_repo=mock_repos["lot"]
    )

# --- TEST SENARYOLARI ---

def test_taslak_irsaliyeden_palet_bilgisi_alinamaz(service, mock_repos):
    # Hazırlık: İrsaliye TASLAK durumunda
    irsaliye = MalKabulIrsaliye(id=1, durum=MalKabulDurum.TASLAK, depo_id=10)
    kalem = MalKabulKalemi(palet_no="P001", mal_kabul_irsaliyesi_id=1, urun_id=5)
    
    mock_repos["mal_kabul"].getir_kalem_palet_no_ile.return_value = kalem
    mock_repos["mal_kabul"].getir_id_ile.return_value = irsaliye

    # İşlem & Doğrulama: GecersizIslemError bekliyoruz (Kritik-3)
    with pytest.raises(GecersizIslemError) as exc:
        service.palet_bilgisi_getir("P001")
    
    assert "Taslak halindeki irsaliyelerden" in str(exc.value)

def test_onayli_irsaliyeden_palet_bilgisi_alinabilir(service, mock_repos):
    # Hazırlık: İrsaliye ONAYLANDI durumunda
    irsaliye = MalKabulIrsaliye(id=1, durum=MalKabulDurum.ONAYLANDI, depo_id=10)
    kalem = MalKabulKalemi(palet_no="P001", mal_kabul_irsaliyesi_id=1, urun_id=5, miktar=10)
    
    mock_repos["mal_kabul"].getir_kalem_palet_no_ile.return_value = kalem
    mock_repos["mal_kabul"].getir_id_ile.return_value = irsaliye
    mock_repos["urun"].getir_id_ile.return_value = MagicMock(isim="Test Urun", barkod="123")
    mock_repos["depo"].getir_id_ile.return_value = MagicMock(isim="Ana Depo")

    # İşlem: Bilgiyi çek
    dto = service.palet_bilgisi_getir("P001")

    # Doğrulama
    assert dto.palet_no == "P001"
    assert dto.miktar == 10

def test_son_palet_girilince_irsaliye_otomatik_tamamlanmali(service, mock_repos):
    # Hazırlık: 2 kalemli irsaliye, biri zaten girilmiş, diğeri bekliyor
    # DÜZELTME: mal_kabul_irsaliyesi_id=1 parametreleri eklendi
    k1 = MalKabulKalemi(palet_no="P1", durum=KalemDurum.GIRIS_YAPILDI, mal_kabul_irsaliyesi_id=1)
    k2 = MalKabulKalemi(palet_no="P2", durum=KalemDurum.BEKLIYOR, mal_kabul_irsaliyesi_id=1)
    
    irsaliye = MalKabulIrsaliye(id=1, durum=MalKabulDurum.ONAYLANDI, kalemler=[k1, k2])
    
    mock_repos["mal_kabul"].getir_kalem_palet_no_ile.return_value = k2
    mock_repos["mal_kabul"].getir_id_ile.return_value = irsaliye

    # İşlem: Son paleti (P2) onayla (Yüksek-1)
    service.palet_giris_onayla("P2")

    # Doğrulama: İrsaliye durumu KAPANDI olmalı
    assert irsaliye.durum == MalKabulDurum.KAPANDI
    mock_repos["mal_kabul"].guncelle.assert_called_once()