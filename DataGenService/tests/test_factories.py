"""Faz 2 — Factory katmanı testleri.

Üç eksen:
  1. Determinism: aynı seed → byte-by-byte aynı çıktı.
  2. Pydantic validasyon: backend kısıtları reddedilir.
  3. Referans bütünlüğü: bağımlı factory'ler parent kayıtları doğru kullanır.
"""

from __future__ import annotations

import pytest

from app.factories import (
    BaseFactory,
    LotFactory,
    PaletFactory,
    RafFactory,
    ReferenceTable,
    SiparisFactory,
    TalepZamanSerisiFactory,
    ToplamaGorevFactory,
    UrunDTO,
    UrunFactory,
    YerlestirmeGorevFactory,
)


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_urun_factory_build_many_deterministic() -> None:
    a = UrunFactory(seed=42).build_many(50)
    b = UrunFactory(seed=42).build_many(50)
    assert [u.model_dump() for u in a] == [u.model_dump() for u in b]


@pytest.mark.unit
def test_urun_factory_different_seed_diverges() -> None:
    a = UrunFactory(seed=42).build_many(20)
    b = UrunFactory(seed=43).build_many(20)
    assert [u.model_dump() for u in a] != [u.model_dump() for u in b]


@pytest.mark.unit
def test_build_one_at_index_matches_build_many_slice() -> None:
    """build_one(k) ve build_many(>k)[k] aynı kaydı vermeli."""
    factory = UrunFactory(seed=7)
    serisi = factory.build_many(10)
    tek = UrunFactory(seed=7).build_one(5)
    assert tek.model_dump() == serisi[5].model_dump()


@pytest.mark.unit
def test_build_many_resets_state_between_calls() -> None:
    factory = UrunFactory(seed=42)
    first = factory.build_many(5)
    second = factory.build_many(5)
    assert [u.model_dump() for u in first] == [u.model_dump() for u in second]


@pytest.mark.unit
def test_negative_count_rejected() -> None:
    with pytest.raises(ValueError, match="count negatif olamaz"):
        UrunFactory(seed=1).build_many(-1)


# ---------------------------------------------------------------------------
# Pydantic validasyon
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_urun_factory_outputs_valid_dto() -> None:
    factory = UrunFactory(seed=42)
    urunler = factory.build_many(100)
    assert len(urunler) == 100
    for urun in urunler:
        assert isinstance(urun, UrunDTO)
        assert 1 <= urun.ic_adet
        assert urun.fiyat >= 0
        assert urun.depolama_tipi in {"Kuru", "Soguk", "Tehlikeli"}
        if urun.ean is not None:
            assert urun.ean.isdigit()
            assert len(urun.ean) in {8, 13, 14}


@pytest.mark.unit
def test_urun_rejects_invalid_override() -> None:
    factory = UrunFactory(seed=42)
    with pytest.raises(Exception):
        factory.build_one(0, fiyat=-5.0)


@pytest.mark.unit
def test_urun_rejects_unknown_field() -> None:
    """extra='forbid' davranışı: bilinmeyen alan reddedilir."""
    factory = UrunFactory(seed=42)
    with pytest.raises(Exception):
        factory.build_one(0, bilinmeyen_alan="x")


# ---------------------------------------------------------------------------
# Referans bütünlüğü — bağımlı factory'ler
# ---------------------------------------------------------------------------


@pytest.fixture()
def urun_pool() -> ReferenceTable:
    pool = ReferenceTable()
    for i, dto in enumerate(UrunFactory(seed=42).build_many(30), start=1):
        pool.add({"id": i, **dto.model_dump()})
    return pool


@pytest.fixture()
def raf_pool() -> ReferenceTable:
    pool = ReferenceTable()
    for i, dto in enumerate(RafFactory(seed=42).build_many(20), start=1):
        pool.add({"id": i, **dto.model_dump()})
    return pool


@pytest.fixture()
def lot_pool(urun_pool: ReferenceTable) -> ReferenceTable:
    factory = LotFactory(seed=42, urun_pool=urun_pool)
    pool = ReferenceTable()
    for i, dto in enumerate(factory.build_many(40), start=1):
        pool.add({"id": i, **dto.model_dump()})
    return pool


@pytest.mark.unit
def test_lot_uses_only_existing_urun_ids(urun_pool: ReferenceTable) -> None:
    factory = LotFactory(seed=42, urun_pool=urun_pool)
    lotlar = factory.build_many(50)
    gecerli_ids = {row["id"] for row in urun_pool}
    for lot in lotlar:
        assert lot.urun_id in gecerli_ids


@pytest.mark.unit
def test_lot_empty_pool_raises() -> None:
    factory = LotFactory(seed=42, urun_pool=ReferenceTable())
    with pytest.raises(ValueError, match="ReferenceTable boş"):
        factory.build_many(5)


@pytest.mark.unit
def test_palet_references_lot_and_raf(
    lot_pool: ReferenceTable, raf_pool: ReferenceTable
) -> None:
    factory = PaletFactory(seed=42, lot_pool=lot_pool, raf_pool=raf_pool)
    paletler = factory.build_many(20)
    gecerli_lot = {row["id"] for row in lot_pool}
    gecerli_raf = {row["id"] for row in raf_pool}
    for palet in paletler:
        assert palet.lot_id in gecerli_lot
        assert palet.raf_id in gecerli_raf
        assert palet.koli_adedi > 0


@pytest.mark.unit
def test_siparis_kalemler_unique_per_order(urun_pool: ReferenceTable) -> None:
    factory = SiparisFactory(
        seed=42, urun_pool=urun_pool, min_kalem=3, max_kalem=3
    )
    siparisler = factory.build_many(10)
    gecerli_ids = {row["id"] for row in urun_pool}
    for siparis in siparisler:
        assert len(siparis.kalemler) == 3
        urunler = [k.urun_id for k in siparis.kalemler]
        assert len(set(urunler)) == 3, "kalemler ürün id'sinde tekrar etmemeli"
        for k in siparis.kalemler:
            assert k.urun_id in gecerli_ids


@pytest.mark.unit
def test_yerlestirme_gorev_uses_pools(
    raf_pool: ReferenceTable, lot_pool: ReferenceTable
) -> None:
    palet_pool = ReferenceTable()
    palet_factory = PaletFactory(seed=11, lot_pool=lot_pool, raf_pool=raf_pool)
    for i, p in enumerate(palet_factory.build_many(10), start=1):
        palet_pool.add({"id": i, **p.model_dump()})

    factory = YerlestirmeGorevFactory(
        seed=42, palet_pool=palet_pool, raf_pool=raf_pool
    )
    gorevler = factory.build_many(15)
    gecerli_palet = {row["id"] for row in palet_pool}
    gecerli_raf = {row["id"] for row in raf_pool}
    for g in gorevler:
        assert g.palet_id in gecerli_palet
        assert g.onerilen_raf_id in gecerli_raf
        assert 1 <= g.oncelik <= 5


@pytest.mark.unit
def test_toplama_gorev_fallback_to_index_when_pool_empty() -> None:
    factory = ToplamaGorevFactory(seed=42)
    gorevler = factory.build_many(5)
    assert [g.sevkiyat_id for g in gorevler] == [1, 2, 3, 4, 5]


# ---------------------------------------------------------------------------
# Talep zaman serisi (ML çıktısı)
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_talep_zaman_serisi_count(urun_pool: ReferenceTable) -> None:
    factory = TalepZamanSerisiFactory(seed=42, urun_pool=urun_pool)
    kayitlar = list(factory.build_series(gun_sayisi=10))
    assert len(kayitlar) == len(urun_pool) * 10


@pytest.mark.unit
def test_talep_zaman_serisi_deterministic(urun_pool: ReferenceTable) -> None:
    a = list(TalepZamanSerisiFactory(seed=99, urun_pool=urun_pool).build_series(gun_sayisi=7))
    b = list(TalepZamanSerisiFactory(seed=99, urun_pool=urun_pool).build_series(gun_sayisi=7))
    assert [k.model_dump() for k in a] == [k.model_dump() for k in b]


@pytest.mark.unit
def test_talep_zaman_serisi_haftanin_gunu_dogru(urun_pool: ReferenceTable) -> None:
    factory = TalepZamanSerisiFactory(seed=42, urun_pool=urun_pool)
    kayitlar = list(factory.build_series(gun_sayisi=14))
    for kayit in kayitlar:
        assert kayit.haftanin_gunu == kayit.tarih.weekday()
        assert 0 <= kayit.haftanin_gunu <= 6
        assert kayit.miktar >= 0


# ---------------------------------------------------------------------------
# BaseFactory soyutlama
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_base_factory_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        BaseFactory(seed=42)  # type: ignore[abstract]
