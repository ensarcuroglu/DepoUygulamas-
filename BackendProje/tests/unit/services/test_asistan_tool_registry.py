"""AsistanToolRegistry birim testleri.

Authoritative DB yazimini test etmiyoruz (executor sahte). Sadece registry
sozlesmesi: register, authorize, execute, RBAC.
"""

from __future__ import annotations

import pytest

from app.application.services.asistan_tool_registry import (
    AsistanToolRegistry,
    ToolExecutionContext,
    ToolExecutionError,
    ToolNotAuthorizedError,
    ToolNotRegisteredError,
    ToolSpec,
)
from core.api_exceptions import BadRequestError

pytestmark = pytest.mark.unit


def _ctx(rol: str = "admin", payload: dict | None = None) -> ToolExecutionContext:
    return ToolExecutionContext(
        kullanici_id=1,
        rol=rol,
        payload=payload or {},
        db=None,  # tool executor'u DB'ye dokunmadigi surece sorun degil
    )


def _ok_executor(context: ToolExecutionContext) -> dict:
    return {"echo": context.payload, "by": context.kullanici_id}


def _spec(
    tool_id: str = "tool_x",
    *,
    hitl: bool = False,
    rbac_roles: tuple[str, ...] = ("admin",),
    executor=_ok_executor,
) -> ToolSpec:
    return ToolSpec(
        tool_id=tool_id,
        aciklama=f"{tool_id} test",
        hitl=hitl,
        rbac_roles=frozenset(rbac_roles),
        executor=executor,
    )


def test_register_and_get():
    registry = AsistanToolRegistry()
    spec = _spec()
    registry.register(spec)
    assert registry.get("tool_x") is spec


def test_register_duplicate_raises():
    registry = AsistanToolRegistry()
    registry.register(_spec())
    with pytest.raises(ValueError):
        registry.register(_spec())


def test_get_or_raise_unknown_raises_tool_not_registered():
    registry = AsistanToolRegistry()
    with pytest.raises(ToolNotRegisteredError):
        registry.get_or_raise("yok")


def test_list_for_role_filters_by_rbac():
    registry = AsistanToolRegistry()
    registry.register(_spec("admin_only", rbac_roles=("admin",)))
    registry.register(_spec("depocu_too", rbac_roles=("admin", "depocu")))
    registry.register(_spec("lojistik_only", rbac_roles=("lojistik",)))

    admin_tools = {s.tool_id for s in registry.list_for_role("admin")}
    depocu_tools = {s.tool_id for s in registry.list_for_role("depocu")}
    lojistik_tools = {s.tool_id for s in registry.list_for_role("lojistik")}

    assert admin_tools == {"admin_only", "depocu_too"}
    assert depocu_tools == {"depocu_too"}
    assert lojistik_tools == {"lojistik_only"}


def test_authorize_denies_unauthorized_role():
    registry = AsistanToolRegistry()
    registry.register(_spec(rbac_roles=("admin",)))
    with pytest.raises(ToolNotAuthorizedError):
        registry.authorize("tool_x", "depocu")


def test_execute_calls_executor_with_context_and_returns_result():
    registry = AsistanToolRegistry()
    registry.register(_spec(rbac_roles=("admin",)))
    context = _ctx(rol="admin", payload={"x": 1})
    sonuc = registry.execute(context, "tool_x")
    assert sonuc == {"echo": {"x": 1}, "by": 1}


def test_execute_unknown_tool_raises():
    registry = AsistanToolRegistry()
    with pytest.raises(ToolNotRegisteredError):
        registry.execute(_ctx(), "yok")


def test_execute_unauthorized_role_raises():
    registry = AsistanToolRegistry()
    registry.register(_spec(rbac_roles=("admin",)))
    with pytest.raises(ToolNotAuthorizedError):
        registry.execute(_ctx(rol="depocu"), "tool_x")


def test_execute_wraps_unknown_exception_as_tool_execution_error():
    registry = AsistanToolRegistry()

    def boom(context):
        raise RuntimeError("uretim hatasi")

    registry.register(_spec(executor=boom))

    with pytest.raises(ToolExecutionError) as exc_info:
        registry.execute(_ctx(), "tool_x")
    assert "uretim hatasi" in exc_info.value.message


def test_execute_propagates_api_exception_without_wrapping():
    registry = AsistanToolRegistry()

    def yetersiz(context):
        raise BadRequestError("eksik parametre")

    registry.register(_spec(executor=yetersiz))

    with pytest.raises(BadRequestError):
        registry.execute(_ctx(), "tool_x")


def test_temizle_clears_all_tools():
    registry = AsistanToolRegistry()
    registry.register(_spec("a"))
    registry.register(_spec("b"))
    registry.temizle()
    assert registry.get("a") is None
    assert registry.get("b") is None
