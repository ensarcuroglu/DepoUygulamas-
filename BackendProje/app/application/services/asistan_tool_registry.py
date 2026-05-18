"""Asistan tool registry.

LLM'in onerdigi `tool_id` -> authoritative use case eslemesini tutar. Tool'lar
Faz 2'de AssistantAiService'in agent gercek cagri uretmeye baslamasiyla
register edilir. Faz 1'de registry **bostur**; bu tasarim hem framework
hazirligini hem de "tetiklenmemis tool yok" garantisini saglar.

RBAC kontrolu burada yapilir. Authoritative DB yazimi, executor'a iletilen
`ToolExecutionContext` icindeki Session uzerinden tool implementasyonu
tarafindan gerceklestirilir.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from core.api_exceptions import (
    APIException,
    BadRequestError,
    PermissionDeniedError,
)


# ---------------------------------------------------------------------------
# Hata tipleri
# ---------------------------------------------------------------------------

class ToolNotRegisteredError(BadRequestError):
    def __init__(self, tool_id: str):
        super().__init__(f"Asistan tool kayitli degil: {tool_id}")
        self.details = {"tool_id": tool_id}


class ToolNotAuthorizedError(PermissionDeniedError):
    def __init__(self, tool_id: str, rol: str):
        super().__init__(f"Bu rol icin tool yetkisi yok: {tool_id} (rol={rol})")
        self.details = {"tool_id": tool_id, "rol": rol}


class ToolExecutionError(APIException):
    def __init__(self, tool_id: str, mesaj: str):
        super().__init__(
            500,
            f"Asistan tool calistirilamadi ({tool_id}): {mesaj}",
            {"tool_id": tool_id},
        )


# ---------------------------------------------------------------------------
# Tool sozlesmesi
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ToolExecutionContext:
    """Authoritative tool calistirildigi context."""

    kullanici_id: int
    rol: str
    payload: dict[str, Any]
    db: Session


ToolExecutor = Callable[[ToolExecutionContext], dict[str, Any]]


@dataclass(frozen=True)
class ToolSpec:
    """Tool registry kayit sozlesmesi."""

    tool_id: str
    aciklama: str
    hitl: bool
    rbac_roles: frozenset[str]
    executor: ToolExecutor

    def authorized_for(self, rol: str) -> bool:
        return rol in self.rbac_roles


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class AsistanToolRegistry:
    """In-process tool kataogu. Faz 2'de tool implementasyonlari register edilir."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        if spec.tool_id in self._tools:
            raise ValueError(f"Tool zaten kayitli: {spec.tool_id}")
        self._tools[spec.tool_id] = spec

    def deregister(self, tool_id: str) -> None:
        self._tools.pop(tool_id, None)

    def temizle(self) -> None:
        """Test isolasyonu icin tum tool'lari sifirla."""
        self._tools.clear()

    def get(self, tool_id: str) -> Optional[ToolSpec]:
        return self._tools.get(tool_id)

    def get_or_raise(self, tool_id: str) -> ToolSpec:
        spec = self._tools.get(tool_id)
        if spec is None:
            raise ToolNotRegisteredError(tool_id)
        return spec

    def list_for_role(self, rol: str) -> list[ToolSpec]:
        return [spec for spec in self._tools.values() if spec.authorized_for(rol)]

    def authorize(self, tool_id: str, rol: str) -> ToolSpec:
        """Tool'u bul ve rol kontrolu yap; ikisi de gecerse spec doner."""
        spec = self.get_or_raise(tool_id)
        if not spec.authorized_for(rol):
            raise ToolNotAuthorizedError(tool_id, rol)
        return spec

    def execute(self, context: ToolExecutionContext, tool_id: str) -> dict[str, Any]:
        """Tool'u rol kontrolu + executor cagrisi ile calistir."""
        spec = self.authorize(tool_id, context.rol)
        try:
            return spec.executor(context)
        except APIException:
            raise
        except Exception as exc:  # noqa: BLE001 - executor sozlesmesi disindaki her hata
            raise ToolExecutionError(tool_id, str(exc)) from exc


# ---------------------------------------------------------------------------
# Modul seviyesi singleton
# ---------------------------------------------------------------------------

_default_registry: AsistanToolRegistry = AsistanToolRegistry()


def get_tool_registry() -> AsistanToolRegistry:
    """Process-wide tool registry singleton'i."""
    return _default_registry
