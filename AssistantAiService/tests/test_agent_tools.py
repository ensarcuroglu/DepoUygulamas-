"""LocalToolRegistry birim testleri.

Authoritative tool yetkilendirmesi BackendProje'de yapilir (bkz. Faz 1 testleri).
Burada AssistantAiService'in local tool kataloğunun RBAC + allowlist filtresini
ve HITL invariant'larini test ediyoruz.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from app.application.agent.tools import (
    LocalToolRegistry,
    ToolSpec,
    compose_proposed_action_ozet,
    default_registry,
    reset_default_registry,
)

pytestmark = pytest.mark.unit


class _DummyArgs(BaseModel):
    x: int = 1


def _readonly_spec(tool_id="t1", roles=("admin",)):
    async def _exec(**kwargs):
        return {"ok": True, **kwargs}

    return ToolSpec(
        tool_id=tool_id,
        description="dummy",
        hitl=False,
        rbac_roles=frozenset(roles),
        args_schema=_DummyArgs,
        executor=_exec,
    )


def _hitl_spec(tool_id="h1", roles=("admin",)):
    return ToolSpec(
        tool_id=tool_id,
        description="dummy hitl",
        hitl=True,
        rbac_roles=frozenset(roles),
        args_schema=_DummyArgs,
        executor=None,
    )


# ---------------------------------------------------------------------------
# Spec invariants
# ---------------------------------------------------------------------------

def test_hitl_spec_with_executor_is_rejected():
    async def _wrong(**_):
        return {}

    with pytest.raises(ValueError):
        ToolSpec(
            tool_id="bad",
            description="x",
            hitl=True,
            rbac_roles=frozenset({"admin"}),
            args_schema=_DummyArgs,
            executor=_wrong,
        )


def test_readonly_spec_without_executor_is_rejected():
    with pytest.raises(ValueError):
        ToolSpec(
            tool_id="bad",
            description="x",
            hitl=False,
            rbac_roles=frozenset({"admin"}),
            args_schema=_DummyArgs,
            executor=None,
        )


# ---------------------------------------------------------------------------
# Registry & RBAC
# ---------------------------------------------------------------------------

def test_register_and_get():
    r = LocalToolRegistry()
    spec = _readonly_spec()
    r.register(spec)
    assert r.get("t1") is spec


def test_register_duplicate_raises():
    r = LocalToolRegistry()
    r.register(_readonly_spec())
    with pytest.raises(ValueError):
        r.register(_readonly_spec())


def test_list_for_role_filters_by_rbac():
    r = LocalToolRegistry()
    r.register(_readonly_spec("admin_only", roles=("admin",)))
    r.register(_readonly_spec("for_all", roles=("admin", "depocu")))
    r.register(_readonly_spec("lojistik_only", roles=("lojistik",)))

    assert {s.tool_id for s in r.list_for_role("depocu")} == {"for_all"}
    assert {s.tool_id for s in r.list_for_role("admin")} == {"admin_only", "for_all"}


def test_to_langchain_tools_applies_role_and_allowlist():
    r = LocalToolRegistry()
    r.register(_readonly_spec("a", roles=("depocu", "admin")))
    r.register(_readonly_spec("b", roles=("depocu",)))
    r.register(_readonly_spec("c", roles=("admin",)))

    # rol=depocu ve allowlist=['a']: yalniz 'a' kalir
    tools = r.to_langchain_tools(rol="depocu", izinli_tool_idleri=["a"])
    assert [t.name for t in tools] == ["a"]

    # allowlist=None: rol filtresi yetiyor
    tools = r.to_langchain_tools(rol="depocu")
    assert sorted(t.name for t in tools) == ["a", "b"]


# ---------------------------------------------------------------------------
# Built-in v1 tools (default registry)
# ---------------------------------------------------------------------------

def test_default_registry_has_v1_tools():
    reset_default_registry()
    r = default_registry()
    ids = {s.tool_id for s in r.list_for_role("admin")}
    assert "tarih_saat_simdi" in ids
    assert "yerlestirme_konum_degistir" in ids


@pytest.mark.asyncio
async def test_tarih_saat_simdi_returns_iso_datetime_and_gun_adi():
    reset_default_registry()
    spec = default_registry().get("tarih_saat_simdi")
    assert spec is not None
    sonuc = await spec.executor(zone_offset_saat=3)
    assert "iso_datetime" in sonuc
    assert sonuc["zone_offset_saat"] == 3
    assert sonuc["gun_adi"] in {
        "Pazartesi", "Sali", "Carsamba", "Persembe", "Cuma", "Cumartesi", "Pazar",
    }


# ---------------------------------------------------------------------------
# Proposed action ozet
# ---------------------------------------------------------------------------

def test_compose_proposed_action_ozet_for_known_tool():
    ozet = compose_proposed_action_ozet(
        "yerlestirme_konum_degistir",
        {"gorev_id": 42, "yeni_konum_kodu": "B-12-3"},
    )
    assert "42" in ozet and "B-12-3" in ozet


def test_compose_proposed_action_ozet_fallback_for_unknown_tool():
    ozet = compose_proposed_action_ozet("yok_tool", {"k": "v"})
    assert "yok_tool" in ozet
    assert "k=v" in ozet
