from __future__ import annotations

from datetime import date

import pytest

from app.application.dto.belge_taslagi_dto import (
    BelgeTaslagiKalemOnayDTO,
    BelgeTaslagiOlusturRequestDTO,
    BelgeTaslagiOnaylaRequestDTO,
    BelgeTaslagiReddetRequestDTO,
)
from app.application.use_cases.belge_taslagi_use_cases import (
    BelgeTaslagiOlusturUseCase,
    BelgeTaslagiOnaylaUseCase,
    BelgeTaslagiReddetUseCase,
)
from app.core.entities.belge_taslagi import BelgeTaslagi, BelgeTaslagiDurum
from app.core.entities.depo import Depo
from app.core.entities.tedarikci import Tedarikci
from app.core.entities.urun import Urun
from app.core.exceptions import GecersizIslemError

pytestmark = pytest.mark.unit


class FakeDb:
    def __init__(self):
        self.commits = 0
        self.rollbacks = 0

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class FakeLogRepo:
    def __init__(self):
        self.logs = []

    def olustur(self, log, auto_commit=True):
        self.logs.append((log, auto_commit))
        return log


class FakeDepoRepo:
    def getir_id_ile(self, depo_id):
        return Depo(id=depo_id, isim="Ana Depo") if depo_id == 1 else None


class FakeTaslakRepo:
    def __init__(self, taslak=None):
        self.taslak = taslak
        self.created = None
        self.updated = None

    def getir_id_ile(self, taslak_id):
        return self.taslak if self.taslak and self.taslak.id == taslak_id else None

    def getir_hepsi(self, **kwargs):
        return [self.taslak] if self.taslak else []

    def olustur(self, taslak, auto_commit=False):
        taslak.id = 1
        self.created = taslak
        self.taslak = taslak
        return taslak

    def guncelle(self, taslak, auto_commit=False):
        self.updated = taslak
        self.taslak = taslak
        return taslak


class FakeMalKabulRepo:
    def __init__(self):
        self.created = None

    def sonraki_irsaliye_no(self):
        return "MKI-2026-00001"

    def olustur(self, irsaliye):
        irsaliye.id = 100
        for index, kalem in enumerate(irsaliye.kalemler, start=1):
            kalem.id = index
            kalem.mal_kabul_irsaliyesi_id = irsaliye.id
        self.created = irsaliye
        return irsaliye


class FakeTedarikciRepo:
    def __init__(self, suppliers=None):
        self.suppliers = suppliers or [Tedarikci(id=10, firma_adi="ACME GIDA")]

    def getir_id_ile(self, tedarikci_id):
        return next((s for s in self.suppliers if s.id == tedarikci_id), None)

    def getir_hepsi(self, skip=0, limit=100, sadece_aktif=True):
        return self.suppliers[:limit]


class FakeUrunRepo:
    def __init__(self, products=None):
        self.products = (
            products
            if products is not None
            else [Urun(id=20, isim="Pirinc", barkod="ABC-1", ean="EAN-1")]
        )

    def getir_id_ile(self, urun_id):
        return next((p for p in self.products if p.id == urun_id), None)

    def getir_barkod_ile(self, barkod):
        return next((p for p in self.products if p.barkod == barkod or p.ean == barkod), None)

    def getir_ean_ile(self, ean):
        return next((p for p in self.products if p.ean == ean), None)

    def getir_hepsi(self, skip=0, limit=50, search=None, **kwargs):
        if not search:
            return self.products[:limit]
        needle = search.casefold()
        return [
            p for p in self.products
            if needle in (p.isim or "").casefold()
            or needle in (p.barkod or "").casefold()
            or needle in (p.ean or "").casefold()
        ][:limit]


def _raw_payload():
    return {
        "status": "ok",
        "taslak": {
            "belge_tipi": "IRSALIYE",
            "tedarikci": {"value": "ACME GIDA", "confidence": 0.9},
            "irsaliye_no": {"value": "IRS-1", "confidence": 0.9},
            "tarih": {"value": "2026-05-11", "confidence": 0.8},
            "kalemler": [
                {
                    "urun_kodu": {"value": "ABC-1", "confidence": 0.9},
                    "ad": {"value": "Pirinc", "confidence": 0.9},
                    "miktar": {"value": 10, "confidence": 0.9},
                    "birim": {"value": "Adet", "confidence": 0.9},
                }
            ],
            "confidence_score": 0.88,
        },
    }


def test_olustur_confidence_ham_jsondan_hesaplar():
    repo = FakeTaslakRepo()
    db = FakeDb()
    uc = BelgeTaslagiOlusturUseCase(repo, FakeDepoRepo(), FakeLogRepo(), db)

    sonuc = uc.execute(
        BelgeTaslagiOlusturRequestDTO(
            ham_json=_raw_payload(),
            depo_id=1,
            olusturan_kullanici_id=5,
        )
    )

    assert sonuc.id == 1
    assert sonuc.confidence_skoru == 0.88
    assert repo.created.durum == BelgeTaslagiDurum.KABUL_BEKLIYOR
    assert db.commits == 1


def test_onayla_explicit_idler_ile_mal_kabul_olusturur():
    taslak = BelgeTaslagi(id=1, ham_json=_raw_payload(), depo_id=1)
    taslak_repo = FakeTaslakRepo(taslak)
    mal_repo = FakeMalKabulRepo()
    db = FakeDb()
    uc = BelgeTaslagiOnaylaUseCase(
        taslak_repo,
        mal_repo,
        FakeTedarikciRepo(),
        FakeDepoRepo(),
        FakeUrunRepo(),
        FakeLogRepo(),
        db,
    )

    sonuc = uc.execute(
        1,
        BelgeTaslagiOnaylaRequestDTO(
            tedarikci_id=10,
            tarih=date(2026, 5, 11),
            kalemler=[
                BelgeTaslagiKalemOnayDTO(
                    urun_id=20,
                    miktar=7,
                    palet_no="PLT-7",
                    lot_no="L-7",
                )
            ],
        ),
        kullanici_id=5,
    )

    assert sonuc.durum == BelgeTaslagiDurum.KABUL_EDILDI
    assert sonuc.mal_kabul_irsaliye_id == 100
    assert mal_repo.created.tedarikci_id == 10
    assert mal_repo.created.kalemler[0].palet_no == "PLT-7"
    assert mal_repo.created.kalemler[0].miktar == 7
    assert db.commits == 1


def test_onayla_raw_docai_payload_ile_eslestirme_yapar():
    taslak = BelgeTaslagi(id=2, ham_json=_raw_payload(), depo_id=1)
    mal_repo = FakeMalKabulRepo()
    uc = BelgeTaslagiOnaylaUseCase(
        FakeTaslakRepo(taslak),
        mal_repo,
        FakeTedarikciRepo(),
        FakeDepoRepo(),
        FakeUrunRepo(),
        FakeLogRepo(),
        FakeDb(),
    )

    sonuc = uc.execute(2, BelgeTaslagiOnaylaRequestDTO(), kullanici_id=5)

    assert sonuc.durum == BelgeTaslagiDurum.KABUL_EDILDI
    assert mal_repo.created.tarih == date(2026, 5, 11)
    assert mal_repo.created.kalemler[0].urun_id == 20
    assert mal_repo.created.kalemler[0].palet_no == "DOC-2-001"


def test_onayla_urun_eslesmezse_hata_verir():
    taslak = BelgeTaslagi(id=3, ham_json=_raw_payload(), depo_id=1)
    uc = BelgeTaslagiOnaylaUseCase(
        FakeTaslakRepo(taslak),
        FakeMalKabulRepo(),
        FakeTedarikciRepo(),
        FakeDepoRepo(),
        FakeUrunRepo(products=[]),
        FakeLogRepo(),
        FakeDb(),
    )

    with pytest.raises(GecersizIslemError, match="Urun eslestirilemedi"):
        uc.execute(3, BelgeTaslagiOnaylaRequestDTO(), kullanici_id=5)


def test_reddet_durumu_gunceller():
    taslak = BelgeTaslagi(id=4, ham_json=_raw_payload(), depo_id=1)
    repo = FakeTaslakRepo(taslak)
    db = FakeDb()

    sonuc = BelgeTaslagiReddetUseCase(repo, FakeLogRepo(), db).execute(
        4,
        BelgeTaslagiReddetRequestDTO(neden="Okunamadi"),
        kullanici_id=5,
    )

    assert sonuc.durum == BelgeTaslagiDurum.REDDEDILDI
    assert db.commits == 1
