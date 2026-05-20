"""Static contract check between AssistantAiService and BackendProje tools."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

from app.application.agent.tools import default_registry, reset_default_registry

pytestmark = pytest.mark.unit


def test_assistant_and_backend_tool_contracts_match():
    reset_default_registry()
    assistant_contract = {
        spec.tool_id: {
            "hitl": spec.hitl,
            "rbac_roles": sorted(spec.rbac_roles),
            "args_schema": spec.args_schema.__name__,
        }
        for spec in default_registry().list_for_role("admin")
    }
    assistant_contract.update(
        {
            spec.tool_id: {
                "hitl": spec.hitl,
                "rbac_roles": sorted(spec.rbac_roles),
                "args_schema": spec.args_schema.__name__,
            }
            for spec in default_registry().list_for_role("depocu")
            if spec.tool_id not in assistant_contract
        }
    )
    assistant_contract.update(
        {
            spec.tool_id: {
                "hitl": spec.hitl,
                "rbac_roles": sorted(spec.rbac_roles),
                "args_schema": spec.args_schema.__name__,
            }
            for spec in default_registry().list_for_role("lojistik")
            if spec.tool_id not in assistant_contract
        }
    )

    backend_contract = _backend_contract()

    assert assistant_contract == backend_contract


def _backend_contract() -> dict[str, dict[str, Any]]:
    root = Path(__file__).resolve().parents[2]
    source = (
        root
        / "BackendProje"
        / "app"
        / "application"
        / "services"
        / "asistan_default_tools.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(source)
    constants = _string_constants(tree)
    roles = _role_constants(tree)
    out: dict[str, dict[str, Any]] = {}

    for call in [n for n in ast.walk(tree) if isinstance(n, ast.Call)]:
        if not isinstance(call.func, ast.Name) or call.func.id != "ToolSpec":
            continue
        kwargs = {kw.arg: kw.value for kw in call.keywords if kw.arg}
        tool_id = _resolve_string(kwargs["tool_id"], constants)
        out[tool_id] = {
            "hitl": _resolve_bool(kwargs["hitl"]),
            "rbac_roles": sorted(_resolve_roles(kwargs["rbac_roles"], roles)),
            "args_schema": _resolve_name(kwargs["args_schema"]),
        }

    return out


def _string_constants(tree: ast.Module) -> dict[str, str]:
    out: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        out[target.id] = node.value.value
    return out


def _role_constants(tree: ast.Module) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        if not isinstance(node.value.func, ast.Name) or node.value.func.id != "frozenset":
            continue
        if not node.value.args or not isinstance(node.value.args[0], ast.Set):
            continue
        values = {
            elt.value
            for elt in node.value.args[0].elts
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
        }
        for target in node.targets:
            if isinstance(target, ast.Name):
                out[target.id] = values
    return out


def _resolve_string(node: ast.AST, constants: dict[str, str]) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return constants[node.id]
    raise AssertionError(f"Unsupported string expression: {ast.dump(node)}")


def _resolve_bool(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant) and isinstance(node.value, bool):
        return node.value
    raise AssertionError(f"Unsupported bool expression: {ast.dump(node)}")


def _resolve_roles(node: ast.AST, roles: dict[str, set[str]]) -> set[str]:
    if isinstance(node, ast.Name):
        return roles[node.id]
    raise AssertionError(f"Unsupported roles expression: {ast.dump(node)}")


def _resolve_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    raise AssertionError(f"Unsupported name expression: {ast.dump(node)}")
