"""
Unit testler: Entity <-> ORM alan uyumu ve mapper tutarliligi (Faz B - B6).
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import date, datetime
import inspect
from typing import Callable, get_type_hints

import pytest
from sqlalchemy.sql import sqltypes

from app.infrastructure.persistence import mappers as mapper_module

pytestmark = pytest.mark.unit


@dataclass(frozen=True)
class MapperPair:
    name: str
    to_entity: Callable
    to_orm: Callable
    orm_cls: type
    entity_cls: type


def _collect_mapper_pairs() -> list[MapperPair]:
    pairs: list[MapperPair] = []

    for attr_name in dir(mapper_module):
        if not attr_name.endswith("_to_entity"):
            continue

        base_name = attr_name[: -len("_to_entity")]
        to_orm_name = f"{base_name}_to_orm"
        if not hasattr(mapper_module, to_orm_name):
            continue

        to_entity = getattr(mapper_module, attr_name)
        to_orm = getattr(mapper_module, to_orm_name)

        hints_to_entity = get_type_hints(to_entity)
        hints_to_orm = get_type_hints(to_orm)

        first_param_name = next(iter(inspect.signature(to_entity).parameters))
        orm_cls = hints_to_entity.get(first_param_name)
        entity_cls = hints_to_entity.get("return")
        orm_return_cls = hints_to_orm.get("return")

        if orm_cls is None or entity_cls is None or orm_return_cls is None:
            continue
        if not is_dataclass(entity_cls):
            continue

        assert orm_cls is orm_return_cls, (
            f"{base_name}: to_entity param ORM sinifi ile to_orm return ORM sinifi ayni olmali. "
            f"{orm_cls} != {orm_return_cls}"
        )

        pairs.append(
            MapperPair(
                name=base_name,
                to_entity=to_entity,
                to_orm=to_orm,
                orm_cls=orm_cls,
                entity_cls=entity_cls,
            )
        )

    return sorted(pairs, key=lambda p: p.name)


MAPPER_PAIRS = _collect_mapper_pairs()


# ORM'de olmayip entity'de bulunmasi bilincli olan alanlar (relation/computed)
ALLOWED_ENTITY_ONLY_FIELDS: dict[str, set[str]] = {
    "Lot": {"urun_isim", "marka_id", "marka_isim"},
    "MalKabulIrsaliye": {
        "kalemler",
        "yerlestirme_gorev_toplam",
        "yerlestirme_gorev_tamamlanan",
        "yerlestirme_gorev_iptal",
    },
    "Palet": {"lot", "raf"},
    "Siparis": {"kalemler"},
    "StokHareketi": {"palet_no"},
    "StokSayim": {"sayim_kalemleri"},
    "Urun": {"stok_miktari"},
    "YerlestirmeGorevi": {"lot_no", "miktar", "onerilen_raf_kodu", "palet_barkodu", "urun_adi", "zone_adi"},
}


def _orm_column_names(orm_cls: type) -> set[str]:
    return {col.name for col in orm_cls.__table__.columns}


def _entity_field_names(entity_cls: type) -> set[str]:
    return {f.name for f in fields(entity_cls)}


def _sample_value_for_column(column, idx: int):
    col_type = column.type
    col_name = column.name

    if isinstance(col_type, sqltypes.Boolean):
        return idx % 2 == 0

    if isinstance(col_type, sqltypes.Integer):
        return idx + 1

    if isinstance(col_type, (sqltypes.Float, sqltypes.Numeric)):
        return float(idx) + 0.5

    if isinstance(col_type, sqltypes.DateTime):
        return datetime(2026, 1, (idx % 28) + 1, 12, 0, 0)

    if isinstance(col_type, sqltypes.Date):
        return date(2026, 1, (idx % 28) + 1)

    if isinstance(col_type, sqltypes.JSON):
        if col_name in {"barkodlar", "alici_emailler"}:
            return [f"{col_name}-{idx}"]
        return {"value": f"{col_name}-{idx}"}

    # String / Text / diger tipler
    if col_name == "rol":
        return "depocu"
    if col_name == "hareket_tipi":
        return "giris"
    return f"{col_name}-{idx}"


@pytest.mark.parametrize("pair", MAPPER_PAIRS, ids=[p.name for p in MAPPER_PAIRS])
def test_entity_orm_alanlari_hizali(pair: MapperPair):
    orm_columns = _orm_column_names(pair.orm_cls)
    entity_fields = _entity_field_names(pair.entity_cls)

    orm_only = orm_columns - entity_fields
    assert not orm_only, (
        f"{pair.name}: ORM'deki su kolonlar entity'de yok: {sorted(orm_only)}. "
        "Yeni ORM kolonu eklendiyse entity + mapper guncellenmeli."
    )

    entity_only = entity_fields - orm_columns
    allowed = ALLOWED_ENTITY_ONLY_FIELDS.get(pair.entity_cls.__name__, set())
    assert entity_only == allowed, (
        f"{pair.name}: Entity-only alanlar beklenenle uyusmuyor. "
        f"Beklenen={sorted(allowed)}, Gelen={sorted(entity_only)}"
    )


@pytest.mark.parametrize("pair", MAPPER_PAIRS, ids=[p.name for p in MAPPER_PAIRS])
def test_mapper_roundtrip_ortak_alanlari_korur(pair: MapperPair):
    orm_columns = list(pair.orm_cls.__table__.columns)
    sample_values = {
        column.name: _sample_value_for_column(column, idx)
        for idx, column in enumerate(orm_columns)
    }

    orm_instance = pair.orm_cls(**sample_values)
    entity = pair.to_entity(orm_instance)

    shared_fields = _orm_column_names(pair.orm_cls) & _entity_field_names(pair.entity_cls)

    # ORM -> Entity alani dogru tasiniyor mu?
    for field_name in shared_fields:
        assert getattr(entity, field_name) == sample_values[field_name], (
            f"{pair.name}: to_entity '{field_name}' alanini beklenen degerle map etmedi."
        )

    # Entity -> ORM geri donusunde ortak alanlar korunuyor mu?
    orm_back = pair.to_orm(entity)
    for field_name in shared_fields:
        assert getattr(orm_back, field_name) == getattr(entity, field_name), (
            f"{pair.name}: to_orm '{field_name}' alanini dogru tasimadi."
        )
